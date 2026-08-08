import { apiClient } from './client';
import type {
  GamePlatform,
  GameDlcs,
  SeriesStructure,
  SeasonStructure,
  UserTitle,
  UserTitleStatus,
} from '@/entities/title';
import type { User } from './users';

export type TitleType = 'game' | 'movie' | 'tv' | 'series' | 'anime' | 'manga' | 'comics' | 'book';

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
  external_id: string;
  title: string;
  original_title?: string;
  release_year?: number;
  poster_url?: string;
  type: TitleType;
  genres: string[];
}

export interface AddUserTitleRequest {
  external_id: string;
  type: TitleType;
  name: string;
  cover_url?: string;
  release_year?: number;
  genres: string[];
  status: string;
  score?: number;
  score_is_manual?: boolean;
  review_text?: string;
  is_spoiler?: boolean;
  finished_at?: string;
  is_completed_100_percent?: boolean;
  game_platform?: GamePlatform | null;
  progress_value?: number | null;
  increment_completion?: boolean;
}

export interface UpdateSeasonRequest {
  status?: UserTitleStatus;
  score?: number;
  clear_score?: boolean;
  review_text?: string;
  is_spoiler?: boolean;
}

export interface UpdateEpisodeRequest {
  status?: UserTitleStatus;
  score?: number;
  clear_score?: boolean;
}

export interface UpdateDlcRequest {
  status?: UserTitleStatus;
  score?: number;
  clear_score?: boolean;
  review_text?: string;
  is_spoiler?: boolean;
}

export const titlesApi = {
  search: (query: string, type: TitleType) =>
    apiClient.get<TitleSearchResult[]>(`/search?q=${encodeURIComponent(query)}&type=${type}`),

  add: (data: AddUserTitleRequest) =>
    apiClient.post<{
      id: number;
      avg_score?: number | null;
      score_is_manual?: boolean;
      score?: number | null;
    }>('/user-titles', data),

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

  updateStatus: (userTitleId: number, status: UserTitleStatus) =>
    apiClient.patch<{
      id: number;
      status: UserTitleStatus;
      finished_at: string | null;
      times_completed: number;
      updated_at: string;
    }>(`/user-titles/${userTitleId}/status`, { status }),

  recordView: (userTitleId: number) =>
    apiClient.post<{ recorded: boolean }>(`/titles/entry/${userTitleId}/view`),

  getViewers: (userTitleId: number) =>
    apiClient.get<ReviewViewsResponse>(`/titles/entry/${userTitleId}/viewers`),

  getStructure: (userTitleId: number) =>
    apiClient.get<SeriesStructure>(`/user-titles/${userTitleId}/structure`),

  getPublicStructure: (userTitleId: number) =>
    apiClient.get<SeriesStructure>(`/titles/entry/${userTitleId}/structure`),

  syncStructure: (userTitleId: number) =>
    apiClient.post<SeriesStructure>(`/user-titles/${userTitleId}/sync-structure`),

  syncSeasonEpisodes: (userTitleId: number, seasonNumber: number, readonly = false) =>
    apiClient.post<SeasonStructure>(
      readonly
        ? `/titles/entry/${userTitleId}/seasons/${seasonNumber}/sync-episodes`
        : `/user-titles/${userTitleId}/seasons/${seasonNumber}/sync-episodes`,
    ),

  updateSeason: (userTitleId: number, seasonNumber: number, data: UpdateSeasonRequest) =>
    apiClient.put<SeriesStructure>(
      `/user-titles/${userTitleId}/seasons/${seasonNumber}`,
      data,
    ),

  updateEpisode: (
    userTitleId: number,
    seasonNumber: number,
    episodeNumber: number,
    data: UpdateEpisodeRequest,
  ) =>
    apiClient.put<SeriesStructure>(
      `/user-titles/${userTitleId}/seasons/${seasonNumber}/episodes/${episodeNumber}`,
      data,
    ),

  resetSeriesScore: (userTitleId: number) =>
    apiClient.post<SeriesStructure>(`/user-titles/${userTitleId}/reset-score`),

  resetSeasonScore: (userTitleId: number, seasonNumber: number) =>
    apiClient.post<SeriesStructure>(
      `/user-titles/${userTitleId}/seasons/${seasonNumber}/reset-score`,
    ),

  getDlcs: (userTitleId: number) =>
    apiClient.get<GameDlcs>(`/user-titles/${userTitleId}/dlcs`),

  getPublicDlcs: (userTitleId: number) =>
    apiClient.get<GameDlcs>(`/titles/entry/${userTitleId}/dlcs`),

  syncDlcs: (userTitleId: number) =>
    apiClient.post<GameDlcs>(`/user-titles/${userTitleId}/sync-dlcs`),

  updateDlc: (userTitleId: number, dlcTitleId: number, data: UpdateDlcRequest) =>
    apiClient.put<GameDlcs>(`/user-titles/${userTitleId}/dlcs/${dlcTitleId}`, data),

  deleteDlcTracking: (userTitleId: number, dlcTitleId: number) =>
    apiClient.delete(`/user-titles/${userTitleId}/dlcs/${dlcTitleId}`),
};
