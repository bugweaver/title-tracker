import { apiClient } from './client';
import type { Title, UserTitleStatus } from '@/entities/title';

export interface RecommendedByUser {
  id: number;
  login: string;
  name: string | null;
  avatar_url: string | null;
}

export interface RecommendationItem {
  title: Title;
  score: number;
  shared_genres: string[];
  recommended_by: RecommendedByUser[];
}

export type CompareBucket = 'both_completed' | 'only_me' | 'only_them' | 'both_other';

export interface LibraryCompareSide {
  status: UserTitleStatus | string | null;
  score: number | null;
  user_title_id: number | null;
}

export interface LibraryCompareItem {
  title: Title;
  me: LibraryCompareSide;
  them: LibraryCompareSide;
}

export interface LibraryCompareResponse {
  other_user: {
    id: number;
    login: string;
    name: string | null;
    avatar_url: string | null;
  };
  counts: Record<CompareBucket, number>;
  bucket: CompareBucket;
  items: LibraryCompareItem[];
}

export const socialApi = {
  getRecommendations: (limit = 20) =>
    apiClient.get<RecommendationItem[]>(`/social/recommendations?limit=${limit}`),

  compareLibraries: (userId: number, bucket: CompareBucket = 'both_completed', limit = 50, offset = 0) =>
    apiClient.get<LibraryCompareResponse>(
      `/users/${userId}/compare?bucket=${bucket}&limit=${limit}&offset=${offset}`,
    ),
};
