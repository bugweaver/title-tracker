import { apiClient } from './client';
import type { Title, UserTitleStatus } from '@/entities/title';

export interface FeedActor {
  id: number;
  login: string;
  name: string | null;
  avatar_url: string | null;
}

export interface FeedItem {
  user_title_id: number;
  event: 'new' | 'updated';
  status: UserTitleStatus | string;
  score: number | null;
  review_preview: string | null;
  created_at: string;
  updated_at: string;
  actor: FeedActor;
  title: Title;
}

export const feedApi = {
  getFeed: (limit = 30, offset = 0) =>
    apiClient.get<FeedItem[]>(`/feed?limit=${limit}&offset=${offset}`),
};
