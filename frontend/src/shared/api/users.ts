import { apiClient } from './client';

export interface User {
  id: number;
  email: string;
  login: string;
  name: string | null;
  avatar_url: string | null;
}

export const usersApi = {
  getUser: (id: number) => apiClient.get<User>(`/users/${id}`),
  uploadAvatar: (file: File) => {
    const formData = new FormData();
    formData.append('avatar', file);
    return apiClient.postFormData<User>('/users/me/avatar', formData);
  },
};
