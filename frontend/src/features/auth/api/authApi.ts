import { apiClient } from '@/shared/api';
import type { User, TokenInfo } from '@/entities/user';

export interface RegisterData {
  email: string;
  login: string;
  password: string;
  name?: string;
}

export interface LoginData {
  username: string;
  password: string;
  [key: string]: string;
}

export const authApi = {
  async register(data: RegisterData): Promise<User> {
    return apiClient.post<User>('/auth/register', data);
  },

  async login(data: LoginData): Promise<TokenInfo> {
    return apiClient.postFormUrlEncoded<TokenInfo>('/auth/login', data);
  },

  async refresh(): Promise<TokenInfo> {
    // No need to pass token - it's in httponly cookie
    return apiClient.post<TokenInfo>('/auth/refresh');
  },

  async logout(): Promise<void> {
    return apiClient.post<void>('/auth/logout');
  },
};
