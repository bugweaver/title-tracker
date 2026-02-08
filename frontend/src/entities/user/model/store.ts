import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import type { User, TokenInfo } from './types';
import { apiClient } from '@/shared/api';

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null);
  const accessToken = ref<string | null>(localStorage.getItem('access_token'));

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value);

  function setTokens(tokens: TokenInfo) {
    accessToken.value = tokens.access_token;
    localStorage.setItem('access_token', tokens.access_token);
    // refresh_token is now in httponly cookie, not stored in JS
  }

  function clearTokens() {
    accessToken.value = null;
    localStorage.removeItem('access_token');
  }

  function setUser(userData: User | null) {
    user.value = userData;
  }

  async function fetchCurrentUser() {
    if (!accessToken.value) return;
    
    try {
      const userData = await apiClient.get<User>('/auth/me');
      setUser(userData);
    } catch {
      // Token might be invalid, clear it and user
      clearTokens();
      setUser(null);
    }
  }

  async function logout() {
    try {
      // Call logout endpoint to clear cookie and redis session
      await apiClient.post('/auth/logout');
    } catch {
      // Ignore errors, clear local state anyway
    } finally {
      clearTokens();
      setUser(null);
    }
  }

  async function initAuth() {
    // Try to restore session on app load
    if (accessToken.value) {
      await fetchCurrentUser();
    }
  }

  return {
    user,
    accessToken,
    isAuthenticated,
    setTokens,
    clearTokens,
    setUser,
    fetchCurrentUser,
    logout,
    initAuth,
  };
});
