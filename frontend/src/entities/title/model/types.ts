export enum TitleCategory {
  GAME = 'game',
  MOVIE = 'movie',
  SERIES = 'series',
  ANIME = 'anime',
  MANGA = 'manga',
  COMICS = 'comics',
  BOOK = 'book',
}

export enum UserTitleStatus {
  COMPLETED = 'completed',
  PLAYING = 'playing',
  WATCHING = 'watching',
  DROPPED = 'dropped',
  PLANNED = 'planned',
  ON_HOLD = 'on_hold',
}

export enum GamePlatform {
  PC = 'PC',
  PLAYSTATION = 'Playstation',
  XBOX = 'Xbox',
  NINTENDO = 'Nintendo',
}

export interface Screenshot {
  id: number;
  url: string;
  position: number;
}

export interface Title {
  id: number;
  name: string;
  category: TitleCategory;
  external_id: string | null;
  cover_image: string | null;
  description: string | null;
  release_year: number | null;
  genres: string[] | null;
}

export interface UserTitle {
  id: number;
  user_id: number;
  title_id: number;
  status: UserTitleStatus;
  score: number | null;
  avg_score: number | null;
  score_is_manual: boolean;
  review_text: string | null;
  is_spoiler: boolean;
  is_completed_100_percent: boolean;
  game_platform: GamePlatform | null;
  times_completed: number;
  created_at: string;
  updated_at: string;
  title: Title;
  finished_at?: string;
  screenshots?: Screenshot[];
  /** Present only for the owner (own list / own review detail). */
  view_count?: number | null;
}

export interface EpisodeStructure {
  id: number | null;
  title_episode_id: number;
  episode_number: number;
  name: string | null;
  status: UserTitleStatus | null;
  score: number | null;
}

export interface SeasonStructure {
  id: number | null;
  title_season_id: number;
  season_number: number;
  name: string | null;
  episode_count: number | null;
  status: UserTitleStatus | null;
  score: number | null;
  avg_score: number | null;
  score_is_manual: boolean;
  review_text: string | null;
  is_spoiler: boolean;
  episodes: EpisodeStructure[];
  episodes_loaded: boolean;
}

export interface SeriesStructure {
  user_title_id: number;
  title_id: number;
  score: number | null;
  avg_score: number | null;
  score_is_manual: boolean;
  status: UserTitleStatus;
  review_text: string | null;
  seasons: SeasonStructure[];
}

