export enum TitleCategory {
  GAME = 'game',
  MOVIE = 'movie',
  SERIES = 'series',
  ANIME = 'anime',
}

export enum UserTitleStatus {
  COMPLETED = 'completed',
  PLAYING = 'playing',
  WATCHING = 'watching',
  DROPPED = 'dropped',
  PLANNED = 'planned',
  ON_HOLD = 'on_hold',
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
  review_text: string | null;
  is_spoiler: boolean;
  created_at: string;
  updated_at: string;
  title: Title;
  finished_at?: string;
  screenshots?: Screenshot[];
}

