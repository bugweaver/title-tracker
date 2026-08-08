import { apiClient } from './client';
import type { Title, UserTitleStatus } from '@/entities/title';

export interface UserListSummary {
  id: number;
  name: string;
  items_count: number;
  created_at: string;
  updated_at: string;
}

export interface UserListItem {
  id: number;
  user_title_id: number;
  position: number;
  status: UserTitleStatus;
  score: number | null;
  progress_value: number | null;
  title: Title;
}

export interface UserListDetail {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
  items: UserListItem[];
}

export const listsApi = {
  list: () => apiClient.get<UserListSummary[]>('/lists/'),

  create: (name: string) =>
    apiClient.post<UserListSummary>('/lists/', { name }),

  get: (listId: number) =>
    apiClient.get<UserListDetail>(`/lists/${listId}`),

  rename: (listId: number, name: string) =>
    apiClient.patch<UserListSummary>(`/lists/${listId}`, { name }),

  remove: (listId: number) =>
    apiClient.delete(`/lists/${listId}`),

  addItem: (listId: number, userTitleId: number) =>
    apiClient.post<UserListDetail>(`/lists/${listId}/items`, {
      user_title_id: userTitleId,
    }),

  removeItem: (listId: number, userTitleId: number) =>
    apiClient.delete(`/lists/${listId}/items/${userTitleId}`),

  reorder: (listId: number, userTitleIds: number[]) =>
    apiClient.put<UserListDetail>(`/lists/${listId}/reorder`, {
      user_title_ids: userTitleIds,
    }),
};
