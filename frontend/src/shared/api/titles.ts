import { apiClient } from './client';
import type { UserTitle } from '@/entities/title';

export type TitleType = 'game' | 'movie' | 'tv' | 'anime';

export interface TitleSearchResult {
  external_id: string; // Changed from id
  title: string;       // Changed from name
  original_title?: string;
  release_year?: number;
  poster_url?: string; // Changed from cover_url
  type: TitleType;     // Added type
  genres: string[];    // Added genres
}

export interface AddUserTitleRequest {
  external_id: string; // Changed from igdb_id
  type: TitleType;
  name: string;
  cover_url?: string;
  release_year?: number;
  genres: string[];
  status: string;
  score?: number;
  review_text?: string;
  is_spoiler?: boolean;
  finished_at?: string;
}

export const titlesApi = {
  search: (query: string, type: TitleType) => 
    apiClient.get<TitleSearchResult[]>(`/search?q=${encodeURIComponent(query)}&type=${type}`),

  add: (data: AddUserTitleRequest) =>
    apiClient.post('/user-titles', data),
    
  getUserTitles: (userId: number) =>
    apiClient.get<UserTitle[]>(`/titles/user/${userId}`),
};
