<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { titlesApi } from '@/shared/api/titles';
import { TitleCategory, UserTitleStatus, type UserTitle } from '@/entities/title';
import UserGameCard from '@/features/games/ui/UserGameCard.vue';
import AppSelect from '@/shared/ui/AppSelect.vue';
import { usersApi, type User } from '@/shared/api';

const route = useRoute();
const userId = computed(() => Number(route.params.id));
const titles = ref<UserTitle[]>([]);
const user = ref<User | null>(null);
const isLoading = ref(false);

const activeTab = ref<TitleCategory>(TitleCategory.GAME);
const activeStatus = ref<UserTitleStatus | 'all'>('all');
const activeYear = ref<number | null>(null);
const activeMonth = ref<number | null>(null);

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

// Filter logic (similar to store but local)
const getTitlesByStatus = (status: UserTitleStatus | 'all', category: TitleCategory) => {
    let filtered = titles.value.filter(t => t.title.category === category);
    if (status !== 'all') {
        filtered = filtered.filter(t => t.status === status);
    }
    return filtered;
};

const getCountByStatus = (status: UserTitleStatus | 'all', category: TitleCategory) => {
      return getTitlesByStatus(status, category).length;
};

const currentStatuses = computed(() => {
  const category = activeTab.value;
  let statuses = [
      'all',
      UserTitleStatus.COMPLETED,
      UserTitleStatus.PLAYING,
      UserTitleStatus.DROPPED,
      UserTitleStatus.PLANNED,
      UserTitleStatus.ON_HOLD,
  ] as const;

  if (category === TitleCategory.MOVIE) {
    // Exclude PLAYING (Watching) for movies
    statuses = statuses.filter(s => s !== UserTitleStatus.PLAYING) as any;
  }

  return statuses.map(status => ({
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
    let filtered = getTitlesByStatus(activeStatus.value, activeTab.value);
    
    if (activeYear.value !== null) {
        filtered = filtered.filter(t => t.finished_at && new Date(t.finished_at).getFullYear() === activeYear.value);
    }
    
    if (activeMonth.value !== null) {
        filtered = filtered.filter(t => t.finished_at && new Date(t.finished_at).getMonth() === activeMonth.value);
    }
    
    
    // Sort by finished_at desc, then by ID desc
    return filtered.sort((a, b) => {
        const dateA = a.finished_at ? new Date(a.finished_at).getTime() : 0;
        const dateB = b.finished_at ? new Date(b.finished_at).getTime() : 0;
        if (dateA !== dateB) {
            return dateB - dateA;
        }
        return b.id - a.id;
    });
});

watch(activeTab, () => {
  activeStatus.value = 'all';
  activeYear.value = null;
  activeMonth.value = null;
});
</script>

<template>
  <div class="max-w-screen-xl mx-auto p-8 flex flex-col gap-7">
    <header class="flex items-center gap-8 p-8 bg-surface border border-border rounded-xl shadow-sm">
       <div class="w-[100px] h-[100px] rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-4xl font-bold border-4 border-background shadow-[0_0_0_2px_var(--color-primary-200)] overflow-hidden">
        <img 
          v-if="user?.avatar_url" 
          :src="user.avatar_url" 
          class="w-full h-full object-cover"
          alt="Avatar"
        />
        <span v-else>{{ user?.login ? user.login.substring(0, 1).toUpperCase() : '#' }}</span>
      </div>
      
      <div>
        <div class="mb-4 leading-tight">
          <h1 class="text-3xl font-bold text-text m-0">{{ user?.name || user?.login || `Пользователь #${userId}` }}</h1>
          <p v-if="user?.name" class="text-text-secondary">@{{ user.login }}</p>
        </div>
        
        <div class="flex gap-8">
          <div class="flex flex-col">
            <span class="text-lg font-bold text-text">{{ titles.length }}</span>
            <span class="text-sm text-text-muted">Тайтлов</span>
          </div>
          <div class="flex flex-col opacity-50">
            <span class="text-lg font-bold text-text">0</span>
            <span class="text-sm text-text-muted">Подписки</span>
          </div>
          <div class="flex flex-col opacity-50">
            <span class="text-lg font-bold text-text">0</span>
            <span class="text-sm text-text-muted">Подписчики</span>
          </div>
        </div>
      </div>
    </header>

    <div class="flex flex-col gap-6">
      <div class="flex gap-2 border-b border-border items-center">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="px-4 py-2 -mb-px border-b-2 font-medium transition-colors duration-200 cursor-pointer text-base"
          :class="[
            activeTab === tab.id
              ? 'border-primary-500 text-primary-500'
              : 'border-transparent text-text-secondary hover:text-text hover:border-border-hover'
          ]"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="flex gap-2 flex-wrap">
        <button
          v-for="status in currentStatuses"
          :key="status.id"
          class="px-3 py-1.5 rounded-full text-sm font-medium transition-colors cursor-pointer"
          :class="[
            activeStatus === status.id
              ? 'bg-primary-100 text-primary-700'
              : 'text-text-secondary hover:bg-background-soft hover:text-text'
          ]"
          @click="activeStatus = status.id"
        >
          {{ status.label }}
          <span class="ml-1.5 opacity-70 text-xs">{{ status.count }}</span>
        </button>
      </div>

      <div v-if="availableYears.length > 0" class="flex gap-2">
         <AppSelect
           v-model="activeYear"
           :options="yearOptions"
           placeholder="Все годы"
           class="w-48"
         />
         <AppSelect
           v-model="activeMonth"
           :options="monthOptions"
           placeholder="Все месяцы"
           class="w-48"
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
        py-16 px-8 bg-background-soft rounded-lg
        border border-border text-center
      ">
      <p class="text-xl text-text mb-2">Список тайтлов пуст</p>
    </div>
  </div>
</template>
