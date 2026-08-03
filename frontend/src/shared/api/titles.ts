import { apiClient } from './client';
import type { GamePlatform, UserTitle } from '@/entities/title';
import type { User } from './users';

export type TitleType = 'game' | 'movie' | 'tv' | 'anime' | 'manga' | 'comics' | 'book';

export interface Screenshot {
  id: number;
  url: string;
  position: number;
}

export interface ReviewViewsResponse {
  count: number;
  viewers: User[];
}

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
  is_completed_100_percent?: boolean;
  game_platform?: GamePlatform | null;
  increment_completion?: boolean;
}

export const titlesApi = {
  search: (query: string, type: TitleType) => 
    apiClient.get<TitleSearchResult[]>(`/search?q=${encodeURIComponent(query)}&type=${type}`),

  add: (data: AddUserTitleRequest) =>
    apiClient.post<{ id: number }>('/user-titles', data),
    
  getUserTitles: (userId: number) =>
    apiClient.get<UserTitle[]>(`/titles/user/${userId}`),

  uploadScreenshot: (userTitleId: number, file: File) => {
    const formData = new FormData();
    formData.append('data', file);
    return apiClient.postFormData<Screenshot>(`/screenshots/upload/${userTitleId}`, formData);
  },

  deleteScreenshot: (screenshotId: number) =>
    apiClient.delete(`/screenshots/${screenshotId}`),

  deleteUserTitle: (userTitleId: number) =>
    apiClient.delete(`/user-titles/${userTitleId}`),

  recordView: (userTitleId: number) =>
    apiClient.post<{ recorded: boolean }>(`/titles/entry/${userTitleId}/view`),

  getViewers: (userTitleId: number) =>
    apiClient.get<ReviewViewsResponse>(`/titles/entry/${userTitleId}/viewers`),
};
