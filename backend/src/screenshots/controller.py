from typing import Annotated, Any

from litestar import Controller, post, delete as litestar_delete, Request
from litestar.di import Provide
from litestar.params import Body
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException, ClientException

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import User, UserTitle, TitleScreenshot
from core.models.db_helper import get_db_session
from core.s3 import s3_service, ALLOWED_CONTENT_TYPES, MAX_FILE_SIZE, MAX_SCREENSHOTS_PER_ENTRY
from .schemas import ScreenshotRead


class ScreenshotsController(Controller):
    path = "/screenshots"
    tags = ["Screenshots"]
    dependencies = {
        "db_session": Provide(get_db_session),
    }

    @post("/upload/{user_title_id:int}")
    async def upload_screenshot(
        self,
        user_title_id: int,
        request: Request[User, dict, Any],  # type: ignore
        db_session: AsyncSession,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> ScreenshotRead:
        """Upload a screenshot for a user title entry."""
        user_id = request.user.id

        # Verify user_title belongs to current user
        stmt = select(UserTitle).where(
            UserTitle.id == user_title_id,
            UserTitle.user_id == user_id,
        )
        result = await db_session.execute(stmt)
        user_title = result.scalar_one_or_none()

        if not user_title:
            raise NotFoundException(detail="Запись не найдена или не принадлежит вам")

        # Check screenshot limit
        count_stmt = select(func.count()).where(
            TitleScreenshot.user_title_id == user_title_id
        )
        count_result = await db_session.execute(count_stmt)
        current_count = count_result.scalar() or 0

        if current_count >= MAX_SCREENSHOTS_PER_ENTRY:
            raise ClientException(
                detail=f"Максимум {MAX_SCREENSHOTS_PER_ENTRY} скриншотов на запись",
                status_code=400,
            )

        # Read and validate file
        content = await data.read()

        if len(content) > MAX_FILE_SIZE:
            raise ClientException(
                detail="Файл слишком большой (макс. 5 МБ)",
                status_code=400,
            )

        content_type = data.content_type or "application/octet-stream"
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ClientException(
                detail=f"Неподдерживаемый формат. Допустимые: JPEG, PNG, WebP, GIF",
                status_code=400,
            )

        # Determine extension
        ext_map = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "image/gif": "gif",
        }
        ext = ext_map.get(content_type, "jpg")

        # Upload to S3
        s3_key = s3_service.generate_key(user_id, ext)
        url = await s3_service.upload_file(content, s3_key, content_type)

        # Save to DB
        screenshot = TitleScreenshot(
            user_title_id=user_title_id,
            url=url,
            s3_key=s3_key,
            position=current_count,
        )
        db_session.add(screenshot)
        await db_session.commit()
        await db_session.refresh(screenshot)

        return ScreenshotRead.model_validate(screenshot)

    @litestar_delete("/{screenshot_id:int}", status_code=200)
    async def delete_screenshot(
        self,
        screenshot_id: int,
        request: Request[User, dict, Any],  # type: ignore
        db_session: AsyncSession,
    ) -> dict[str, bool]:
        """Delete a screenshot."""
        user_id = request.user.id

        # Find screenshot and verify ownership
        stmt = (
            select(TitleScreenshot)
            .join(UserTitle, TitleScreenshot.user_title_id == UserTitle.id)
            .where(
                TitleScreenshot.id == screenshot_id,
                UserTitle.user_id == user_id,
            )
        )
        result = await db_session.execute(stmt)
        screenshot = result.scalar_one_or_none()

        if not screenshot:
            raise NotFoundException(detail="Скриншот не найден")

        # Delete from S3
        await s3_service.delete_file(screenshot.s3_key)

        # Delete from DB
        await db_session.delete(screenshot)
        await db_session.commit()

        return {"success": True}
