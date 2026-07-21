<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { titlesApi } from '@/shared/api/titles';
import {
  TitleCategory,
  UserTitleStatus,
  type UserTitle,
  getTitleCategoryFromRouteSegment,
  getTitleCategoryRouteSegment,
  getAvailableTitleStatuses,
  getTitleStatusFromRouteSegment,
  getTitleStatusRouteSegment,
} from '@/entities/title';
import UserGameCard from '@/features/games/ui/UserGameCard.vue';
import AppSelect from '@/shared/ui/AppSelect.vue';
import { usersApi, type UserProfile } from '@/shared/api';
import { useUserStore } from '@/entities/user';

const route = useRoute();
const userStore = useUserStore();
const userId = computed(() => Number(route.params.id));
const titles = ref<UserTitle[]>([]);
const user = ref<UserProfile | null>(null);
const isLoading = ref(false);
const followLoading = ref(false);

const isOwnProfile = computed(() => userStore.user?.id === userId.value);

const activeYear = ref<number | null>(null);
const activeMonth = ref<number | null>(null);

const activeTab = computed(() => getTitleCategoryFromRouteSegment(route.params.category));
const activeStatus = computed(() => getTitleStatusFromRouteSegment(route.params.status, activeTab.value));

const getTabRoute = (category: TitleCategory) => ({
  name: 'user-profile',
  params: {
    id: route.params.id,
    category: getTitleCategoryRouteSegment(category),
    status: undefined,
  },
});

const getStatusRoute = (status: UserTitleStatus | 'all') => ({
  name: 'user-profile',
  params: {
    id: route.params.id,
    category: getTitleCategoryRouteSegment(activeTab.value),
    status: status === 'all' ? undefined : getTitleStatusRouteSegment(status),
  },
});

const fetchUser = async () => {
  try {
    user.value = await usersApi.getUser(userId.value);
  } catch (e) {
    console.error('Failed to fetch user', e);
  }
};

const fetchTitles = async () => {
    isLoading.value = true;
    try {
        titles.value = await titlesApi.getUserTitles(userId.value);
    } catch (e) {
        console.error(e);
    } finally {
        isLoading.value = false;
    }
}

const toggleFollow = async () => {
  if (!user.value || followLoading.value) return;
  followLoading.value = true;
  try {
    if (user.value.is_following) {
      await usersApi.unfollow(userId.value);
      user.value.is_following = false;
      user.value.followers_count--;
    } else {
      await usersApi.follow(userId.value);
      user.value.is_following = true;
      user.value.followers_count++;
    }
  } catch (e) {
    console.error('Follow action failed', e);
  } finally {
    followLoading.value = false;
  }
};

onMounted(() => {
    fetchUser();
    fetchTitles();
});

watch(userId, () => {
    fetchUser();
    fetchTitles();
});

const tabs = [
  { id: TitleCategory.GAME, label: 'Игры' },
  { id: TitleCategory.MOVIE, label: 'Фильмы' },
  { id: TitleCategory.SERIES, label: 'Сериалы' },
  { id: TitleCategory.ANIME, label: 'Аниме' },
] as const;

const getStatusLabel = (status: UserTitleStatus | 'all', category: TitleCategory) => {
    if (status === 'all') return 'Все';
    if (status === UserTitleStatus.COMPLETED) return category === TitleCategory.GAME ? 'Прошел' : 'Посмотрел';
    if (status === UserTitleStatus.PLAYING) return category === TitleCategory.GAME ? 'Играю' : 'Смотрю';
    if (status === UserTitleStatus.WATCHING) return 'Смотрю';
    if (status === UserTitleStatus.DROPPED) return 'Дропнул';
    if (status === UserTitleStatus.PLANNED) return 'В планах';
    if (status === UserTitleStatus.ON_HOLD) return 'На паузе';
    return status;
};

// "Playing" and "Watching" are equivalent for non-game categories (both mean "Смотрю").
// Data may have either value depending on how it was added.
const isWatchingGroup = (s: UserTitleStatus) =>
    s === UserTitleStatus.PLAYING || s === UserTitleStatus.WATCHING;

// Filter logic (similar to store but local)
const getTitlesByStatus = (status: UserTitleStatus | 'all', category: TitleCategory) => {
    let filtered = titles.value.filter(t => t.title.category === category);
    if (status !== 'all') {
        if (category !== TitleCategory.GAME && isWatchingGroup(status)) {
            // Match both "playing" and "watching" for non-game categories
            filtered = filtered.filter(t => isWatchingGroup(t.status));
        } else {
            filtered = filtered.filter(t => t.status === status);
        }
    }
    return filtered;
};

const filterByFinishedPeriod = (sourceTitles: UserTitle[]) => {
    if (activeYear.value === null && activeMonth.value === null) {
        return sourceTitles;
    }

    return sourceTitles.filter((title) => {
        if (!title.finished_at) {
            return false;
        }

        const date = new Date(title.finished_at);

        if (activeYear.value !== null && date.getFullYear() !== activeYear.value) {
            return false;
        }

        if (activeMonth.value !== null && date.getMonth() !== activeMonth.value) {
            return false;
        }

        return true;
    });
};

const getCountByStatus = (status: UserTitleStatus | 'all', category: TitleCategory) => {
      return filterByFinishedPeriod(getTitlesByStatus(status, category)).length;
};

const currentStatuses = computed(() => {
  const category = activeTab.value;

  return getAvailableTitleStatuses(category).map(status => ({
    id: status,
    label: getStatusLabel(status, category),
    count: getCountByStatus(status, category)
  }));
});

const availableYears = computed(() => {
    const categoryTitles = titles.value.filter(t => t.title.category === activeTab.value);
    const years = new Set<number>();
    
    categoryTitles.forEach(t => {
        if (t.finished_at) {
            years.add(new Date(t.finished_at).getFullYear());
        }
    });
    
    return Array.from(years).sort((a, b) => b - a);
});

const yearOptions = computed(() => {
    return [
        { value: null, label: 'Все годы' },
        ...availableYears.value.map(y => ({ value: y, label: String(y) }))
    ];
});

const monthOptions = computed(() => [
    { value: null, label: 'Все месяцы' },
    { value: 0, label: 'Январь' },
    { value: 1, label: 'Февраль' },
    { value: 2, label: 'Март' },
    { value: 3, label: 'Апрель' },
    { value: 4, label: 'Май' },
    { value: 5, label: 'Июнь' },
    { value: 6, label: 'Июль' },
    { value: 7, label: 'Август' },
    { value: 8, label: 'Сентябрь' },
    { value: 9, label: 'Октябрь' },
    { value: 10, label: 'Ноябрь' },
    { value: 11, label: 'Декабрь' },
]);

const displayedTitles = computed(() => {
    // Create a copy to avoid mutating the source
    const filtered = filterByFinishedPeriod([
        ...getTitlesByStatus(activeStatus.value, activeTab.value),
    ]);
    
    
    // Sort by "Smart Date" (finished_at OR updated_at) desc, then by ID desc
    return filtered.sort((a, b) => {
        // Use finished_at if available (preserve completion history), otherwise updated_at (activity feed)
        const getSortDate = (t: typeof a) => t.finished_at ? new Date(t.finished_at) : new Date(t.updated_at);
        
        const dateA = getSortDate(a);
        const dateB = getSortDate(b);

        const timeA = dateA.getFullYear() * 100 + dateA.getMonth();
        const timeB = dateB.getFullYear() * 100 + dateB.getMonth();

        if (timeA !== timeB) {
            return timeB - timeA;
        }
        return b.id - a.id;
    });
});

watch(activeTab, () => {
  activeYear.value = null;
  activeMonth.value = null;
});
</script>

<template>
  <div class="mx-auto flex max-w-screen-xl flex-col gap-5 p-3 sm:gap-7 sm:p-6 lg:p-8">
    <header class="flex flex-col items-center gap-4 rounded-xl border border-border bg-surface p-4 text-center shadow-sm sm:flex-row sm:gap-8 sm:p-8 sm:text-left">
       <div class="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-full border-4 border-background bg-primary-100 text-3xl font-bold text-primary-600 shadow-[0_0_0_2px_var(--color-primary-200)] sm:h-[100px] sm:w-[100px] sm:text-4xl">
        <img 
          v-if="user?.avatar_url" 
          :src="user.avatar_url" 
          class="w-full h-full object-cover"
          alt="Avatar"
        />
        <span v-else>{{ user?.login ? user.login.substring(0, 1).toUpperCase() : '#' }}</span>
      </div>
      
      <div class="min-w-0 flex-grow">
        <div class="mb-4 leading-tight">
          <h1 class="m-0 break-words text-2xl font-bold text-text sm:text-3xl">{{ user?.name || user?.login || `Пользователь #${userId}` }}</h1>
          <p v-if="user?.name" class="text-text-secondary">@{{ user.login }}</p>
        </div>
        
        <div class="flex justify-center gap-5 sm:justify-start sm:gap-8">
          <div class="flex flex-col">
            <span class="text-lg font-bold text-text">{{ titles.length }}</span>
            <span class="text-sm text-text-muted">Тайтлов</span>
          </div>
          <RouterLink :to="`/user/${userId}/connections?tab=following`" class="stat-link flex flex-col">
            <span class="text-lg font-bold text-text">{{ user?.following_count ?? 0 }}</span>
            <span class="text-sm text-text-muted">Подписки</span>
          </RouterLink>
          <RouterLink :to="`/user/${userId}/connections?tab=followers`" class="stat-link flex flex-col">
            <span class="text-lg font-bold text-text">{{ user?.followers_count ?? 0 }}</span>
            <span class="text-sm text-text-muted">Подписчики</span>
          </RouterLink>
        </div>
      </div>

      <button
        v-if="!isOwnProfile"
        class="follow-btn"
        :class="{ 'follow-btn--following': user?.is_following }"
        :disabled="followLoading"
        @click="toggleFollow"
      >
        {{ user?.is_following ? 'Отписаться' : 'Подписаться' }}
      </button>
    </header>

    <div class="flex flex-col gap-6">
      <div class="flex items-center gap-1 overflow-x-auto border-b border-border [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:gap-2">
        <RouterLink
          v-for="tab in tabs"
          :key="tab.id"
          :to="getTabRoute(tab.id)"
          class="-mb-px min-h-11 shrink-0 cursor-pointer whitespace-nowrap border-b-2 px-4 py-2 font-medium transition-colors duration-200"
          :class="[
            activeTab === tab.id
              ? 'border-primary-500 text-primary-500'
              : 'border-transparent text-text-secondary hover:text-text hover:border-border-hover'
          ]"
        >
          {{ tab.label }}
        </RouterLink>
      </div>

      <div class="flex flex-wrap gap-2">
        <RouterLink
          v-for="status in currentStatuses"
          :key="status.id"
          :to="getStatusRoute(status.id)"
          class="flex min-h-10 cursor-pointer items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-colors"
          :class="[
            activeStatus === status.id
              ? 'bg-primary-100 text-primary-700'
              : 'text-text-secondary hover:bg-background-soft hover:text-text'
          ]"
        >
          {{ status.label }}
          <span class="text-xs opacity-70">{{ status.count }}</span>
        </RouterLink>
      </div>

      <div v-if="availableYears.length > 0" class="grid grid-cols-2 gap-2 sm:flex">
         <AppSelect
           v-model="activeYear"
           :options="yearOptions"
           placeholder="Все годы"
           class="min-w-0 sm:w-48"
         />
         <AppSelect
           v-model="activeMonth"
           :options="monthOptions"
           placeholder="Все месяцы"
           class="min-w-0 sm:w-48"
         />
      </div>
    </div>

    <div v-if="isLoading" class="flex justify-center p-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
    </div>

    <div v-else-if="displayedTitles.length > 0" class="flex flex-col gap-4">
      <UserGameCard 
        v-for="userTitle in displayedTitles" 
        :key="userTitle.id"
        :user-title="userTitle"
      />
    </div>

    <div v-else class="
        flex flex-col items-center justify-center
        py-12 px-4 sm:py-16 sm:px-8 bg-background-soft rounded-lg
        border border-border text-center
      ">
      <p class="text-xl text-text mb-2">Список тайтлов пуст</p>
    </div>
  </div>
</template>

<style scoped>
.follow-btn {
  padding: 10px 24px;
  border-radius: 9999px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  flex-shrink: 0;
  align-self: center;
  white-space: nowrap;
  min-height: 44px;
  transition: all 0.2s;
  background: var(--color-primary-500);
  border: 1px solid var(--color-primary-500);
  color: white;
}

@media (max-width: 639px) {
  .follow-btn {
    width: 100%;
  }
}

.follow-btn:hover {
  background: var(--color-primary-600);
}

.follow-btn--following {
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  color: var(--color-text);
}

.follow-btn--following:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
  color: #ef4444;
}

.stat-link {
  text-decoration: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  margin: -4px -8px;
  transition: background 0.15s;
}

.stat-link:hover {
  background: var(--color-surface-hover, rgba(255, 255, 255, 0.05));
}
</style>
