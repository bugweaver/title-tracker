
import asyncio
import sys
from pathlib import Path

# Add src to python path to allow imports
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent.parent # Adjusted path: backend/src
sys.path.append(str(src_dir / 'src'))

from sqlalchemy import select, update
from core.models.db_helper import db_helper
from core.models.title import Title, TitleCategory
from core.igdb_service import igdb_service
from core.tmdb_service import TmdbService
from core.shikimori_service import ShikimoriService

async def sync_genres():
    print("Starting genre synchronization...")
    
    # Initialize services
    tmdb_movie = TmdbService("movie")
    tmdb_tv = TmdbService("tv")
    shikimori_svc = ShikimoriService()
    
    async with db_helper.session_factory() as session:
        # Fetch all titles regardless of genres to check/update
        stmt = select(Title)
        result = await session.execute(stmt)
        titles = result.scalars().all()
        
        print(f"Found {len(titles)} titles in database.")
        
        updated_count = 0
        
        for title in titles:
            if not title.external_id:
                print(f"Skipping '{title.name}' (No external_id)")
                continue

            # Only update if genres are missing or empty
            if title.genres and len(title.genres) > 0:
                 print(f"Skipping '{title.name}' (Already has {len(title.genres)} genres)")
                 continue

            print(f"Processing '{title.name}' [{title.category}] (ID: {title.external_id})...")
            
            try:
                details = None
                
                if title.category == TitleCategory.GAME:
                    details = await igdb_service.get_details(title.external_id)
                elif title.category == TitleCategory.MOVIE:
                    details = await tmdb_movie.get_details(title.external_id)
                elif title.category == TitleCategory.SERIES:
                    details = await tmdb_tv.get_details(title.external_id)
                elif title.category == TitleCategory.ANIME:
                    details = await shikimori_svc.get_details(title.external_id)
                
                if details and details.genres:
                    # Update genres
                    title.genres = details.genres
                    updated_count += 1
                    print(f"  -> Updated genres: {details.genres}")
                else:
                    print("  -> No genres found or fetch failed.")
                    
            except Exception as e:
                print(f"  -> Error processing '{title.name}': {e}")
        
        if updated_count > 0:
            await session.commit()
            print(f"Successfully committed updates for {updated_count} titles.")
        else:
            print("No updates made.")

    # Dispose engine
    await db_helper.dispose()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(sync_genres())
