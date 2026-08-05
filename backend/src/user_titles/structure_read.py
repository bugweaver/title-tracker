from core.models import TitleSeason, UserTitle, UserTitleEpisode, UserTitleSeason
from .schemas import (
    EpisodeStructureRead,
    SeasonStructureRead,
    SeriesStructureRead,
)


def build_structure_response(
    user_title: UserTitle,
    catalog_seasons: list[TitleSeason],
    user_seasons_by_catalog_id: dict[int, UserTitleSeason],
) -> SeriesStructureRead:
    seasons_out: list[SeasonStructureRead] = []
    for catalog_season in sorted(catalog_seasons, key=lambda s: s.season_number):
        user_season = user_seasons_by_catalog_id.get(catalog_season.id)
        catalog_episodes = list(catalog_season.episodes or [])
        episodes_loaded = len(catalog_episodes) > 0

        episodes_out: list[EpisodeStructureRead] = []
        user_episodes_by_catalog_id: dict[int, UserTitleEpisode] = {}
        if user_season:
            user_episodes_by_catalog_id = {
                ue.title_episode_id: ue for ue in (user_season.episodes or [])
            }

        for catalog_ep in sorted(catalog_episodes, key=lambda e: e.episode_number):
            user_ep = user_episodes_by_catalog_id.get(catalog_ep.id)
            episodes_out.append(
                EpisodeStructureRead(
                    id=user_ep.id if user_ep else None,
                    title_episode_id=catalog_ep.id,
                    episode_number=catalog_ep.episode_number,
                    name=catalog_ep.name,
                    status=user_ep.status if user_ep else None,
                    score=user_ep.score if user_ep else None,
                )
            )

        seasons_out.append(
            SeasonStructureRead(
                id=user_season.id if user_season else None,
                title_season_id=catalog_season.id,
                season_number=catalog_season.season_number,
                name=catalog_season.name,
                episode_count=catalog_season.episode_count,
                status=user_season.status if user_season else None,
                score=user_season.score if user_season else None,
                avg_score=user_season.avg_score if user_season else None,
                score_is_manual=user_season.score_is_manual if user_season else False,
                review_text=user_season.review_text if user_season else None,
                is_spoiler=user_season.is_spoiler if user_season else False,
                episodes=episodes_out,
                episodes_loaded=episodes_loaded,
            )
        )

    return SeriesStructureRead(
        user_title_id=user_title.id,
        title_id=user_title.title_id,
        score=user_title.score,
        avg_score=user_title.avg_score,
        score_is_manual=user_title.score_is_manual,
        status=user_title.status,
        review_text=user_title.review_text,
        seasons=seasons_out,
    )
