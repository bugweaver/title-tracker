import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiClient } from '@/shared/api';
import type { UserTitle } from './types';
import { TitleCategory, UserTitleStatus } from './types';

export const useTitleStore = defineStore('title', () => {
  const titles = ref<UserTitle[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  const fetchMyTitles = async () => {
    isLoading.value = true;
    error.value = null;
    try {
      const response = await apiClient.get<UserTitle[]>('/titles/my');
      titles.value = response;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch titles';
    } finally {
      isLoading.value = false;
    }
  };

  const getTitlesByCategory = (category: TitleCategory) => {
    return titles.value.filter((t) => t.title.category === category);
  };

  // "Playing" and "Watching" are equivalent for non-game categories (both mean "Смотрю")
  const isWatchingGroup = (s: UserTitleStatus) =>
    s === UserTitleStatus.PLAYING || s === UserTitleStatus.WATCHING;

  const getTitlesByStatus = (status: UserTitleStatus | 'all', category?: TitleCategory) => {
    let filtered = titles.value;
    
    if (category) {
      filtered = filtered.filter((t) => t.title.category === category);
    }
    
    if (status === 'all') {
      return filtered;
    }

    // For non-game categories, match both "playing" and "watching"
    if (category && category !== TitleCategory.GAME && isWatchingGroup(status)) {
      return filtered.filter((t) => isWatchingGroup(t.status));
    }
    
    return filtered.filter((t) => t.status === status);
  };
  
  // Helpers for counting
  const getCountByStatus = (status: UserTitleStatus | 'all', category: TitleCategory) => {
      return getTitlesByStatus(status, category).length;
  };

  return {
    titles,
    isLoading,
    error,
    fetchMyTitles,
    getTitlesByCategory,
    getTitlesByStatus,
    getCountByStatus
  };
});
