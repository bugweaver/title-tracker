import { apiClient } from './client';

export interface User {
  id: number;
  email: string;
  login: string;
  name: string | null;
  avatar_url: string | null;
  bio: string | null;
  is_private: boolean;
}

export interface UserProfile extends User {
  followers_count: number;
  following_count: number;
  is_following: boolean;
}

export interface UserProfileUpdate {
  name?: string | null;
  bio?: string | null;
  is_private?: boolean;
}

export interface FollowStatus {
  is_following: boolean;
}

export const usersApi = {
  getUser: (id: number) => apiClient.get<UserProfile>(`/users/${id}`),
  updateProfile: (data: UserProfileUpdate) =>
    apiClient.patch<User>('/users/me', data),
  uploadAvatar: (file: File) => {
    const formData = new FormData();
    formData.append('avatar', file);
    return apiClient.postFormData<User>('/users/me/avatar', formData);
  },
  follow: (userId: number) =>
    apiClient.post<FollowStatus>(`/users/${userId}/follow`),
  unfollow: (userId: number) =>
    apiClient.delete<FollowStatus>(`/users/${userId}/follow`),
  getFollowers: (userId: number) =>
    apiClient.get<User[]>(`/users/${userId}/followers`),
  getFollowing: (userId: number) =>
    apiClient.get<User[]>(`/users/${userId}/following`),
};
