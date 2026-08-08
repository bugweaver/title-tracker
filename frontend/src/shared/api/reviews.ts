import { apiClient } from './client';
import type { User } from './users';

export type ReactionType = 'like' | 'love' | 'laugh' | 'wow' | 'sad';

export interface ReviewComment {
  id: number;
  user_title_id: number;
  body: string;
  created_at: string;
  updated_at: string;
  author: User;
}

export interface ReviewReactions {
  counts: Partial<Record<ReactionType, number>>;
  my_reaction: ReactionType | null;
  total: number;
}

export const reviewsApi = {
  listComments: (userTitleId: number) =>
    apiClient.get<ReviewComment[]>(`/titles/entry/${userTitleId}/comments`),

  createComment: (userTitleId: number, body: string) =>
    apiClient.post<ReviewComment>(`/titles/entry/${userTitleId}/comments`, { body }),

  deleteComment: (userTitleId: number, commentId: number) =>
    apiClient.delete(`/titles/entry/${userTitleId}/comments/${commentId}`),

  getReactions: (userTitleId: number) =>
    apiClient.get<ReviewReactions>(`/titles/entry/${userTitleId}/reactions`),

  setReaction: (userTitleId: number, type: ReactionType) =>
    apiClient.put<ReviewReactions>(`/titles/entry/${userTitleId}/reactions`, { type }),

  deleteReaction: (userTitleId: number) =>
    apiClient.delete(`/titles/entry/${userTitleId}/reactions`),
};
