import { apiClient } from './client';

export interface GameSearchResult {
  id: number;
  name: string;
  release_year?: number;
  cover_url?: string;
  genres: string[];
}

export interface AddUserGameRequest {
  igdb_id: string;
  name: string;
  cover_url?: string;
  release_year?: number;
  genres: string[];
  status: string;
  score?: number;
  review_text?: string;
}

export const gamesApi = {
  search: (query: string) => 
    apiClient.get<GameSearchResult[]>(`/games/search?q=${encodeURIComponent(query)}`),

  add: (data: AddUserGameRequest) =>
    apiClient.post('/user-titles', data),
};
