import { apiClient } from './client';

export interface NotificationActor {
  id: number;
  login: string;
  name: string | null;
  avatar_url: string | null;
}

export interface NotificationTitle {
  id: number;
  name: string;
  cover_image: string | null;
  category: string;
}

export interface NotificationData {
  id: number;
  type: string;
  is_read: boolean;
  created_at: string;
  user_title_id: number | null;
  actor: NotificationActor;
  title: NotificationTitle | null;
}

export interface UnreadCountResponse {
  count: number;
}

export const notificationsApi = {
  getNotifications: (limit = 30, offset = 0) =>
    apiClient.get<NotificationData[]>(`/notifications/?limit=${limit}&offset=${offset}`),

  getUnreadCount: () =>
    apiClient.get<UnreadCountResponse>('/notifications/unread-count'),

  markAsRead: (id: number) =>
    apiClient.request<NotificationData>(`/notifications/${id}/read`, { method: 'PATCH' }),

  markAllAsRead: () =>
    apiClient.request<{ status: string }>('/notifications/read-all', { method: 'PATCH' }),

  clearRead: () =>
    apiClient.delete<{ status: string }>('/notifications/clear'),
};
