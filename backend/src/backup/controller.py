from datetime import datetime
from typing import Annotated, Any

from litestar import Controller, get, post, Request, Response
from litestar.di import Provide
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.models.title import Title, UserTitle
from core.models.db_helper import get_db_session
from core.models import User

from .schemas import BackupItem, BackupResponse
import json

class BackupController(Controller):
    path = "/backup"
    tags = ["Backup"]
    dependencies = {
        "db_session": Provide(get_db_session),
    }

    @get("/export")
    async def export_backup(
        self,
        request: Request[User, dict, Any],
        db_session: AsyncSession,
    ) -> Response:
        """Export all user titles to a JSON file."""
        user = request.user
        stmt = (
            select(UserTitle, Title)
            .join(Title, UserTitle.title_id == Title.id)
            .where(UserTitle.user_id == user.id)
        )
        result = await db_session.execute(stmt)
        rows = result.all()

        backup_data = []
        for user_title, title in rows: # type: UserTitle, Title
            item = BackupItem(
                # Title Data
                external_id=title.external_id,
                type=title.category,
                title=title.name,
                poster_url=title.cover_image,
                release_year=title.release_year,
                genres=title.genres,

                # UserTitle Data
                status=user_title.status,
                score=user_title.score,
                review_text=user_title.review_text,
            )
            backup_data.append(item.model_dump(mode="json"))

        json_content = json.dumps(backup_data, indent=2, ensure_ascii=False)
        filename = f"backup_{datetime.now().strftime('%Y-%m-%d')}.txt"
        
        return Response(
            content=json_content.encode("utf-8"),
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    @post("/import")
    async def import_backup(
        self,
        request: Request[User, dict, Any],
        db_session: AsyncSession,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> BackupResponse:
        """Import user titles from a backup file."""
        user = request.user
        content = await data.read()
        try:
            items_data = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError:
            return BackupResponse(message="Invalid JSON file", processed_count=0)

        processed_count = 0
        
        for item_data in items_data:
            item = BackupItem(**item_data)
            
            # 1. Provide/Find Title
            # We try to find by external_id and type first if available
            title_id = None
            
            if item.external_id:
                stmt = select(Title).where(
                    Title.external_id == item.external_id, 
                    Title.category == item.type
                )
                result = await db_session.execute(stmt)
                existing_title = result.scalar_one_or_none()
                
                if existing_title:
                    title_id = existing_title.id
            
            # If not found by external_id, or no external_id provided, 
            # ideally we should check by name? But name is not unique.
            # Requirements say: "Create (if not exists)... don't make external requests"
            
            if not title_id:
                # Create new title
                new_title = Title(
                    name=item.title,
                    category=item.type,
                    external_id=item.external_id,
                    cover_image=item.poster_url,
                    release_year=item.release_year,
                    genres=item.genres,
                )
                db_session.add(new_title)
                await db_session.flush() # to get ID
                title_id = new_title.id

            # 2. Upsert UserTitle
            # We use postgresql ON CONFLICT to upsert
            stmt = pg_insert(UserTitle).values(
                user_id=user.id,
                title_id=title_id,
                status=item.status,
                score=item.score,
                review_text=item.review_text,
            ).on_conflict_do_update(
                index_elements=["user_id", "title_id"], # Constraint name or columns
                set_={
                    "status": item.status,
                    "score": item.score,
                    "review_text": item.review_text,
                    "updated_at": datetime.now(),
                }
            )
            
            await db_session.execute(stmt)
            processed_count += 1

        await db_session.commit()
        return BackupResponse(message="Backup imported successfully", processed_count=processed_count)
