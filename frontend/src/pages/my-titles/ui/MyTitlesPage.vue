<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue';
import { useUserStore } from '@/entities/user';
import { useTitleStore, TitleCategory, UserTitleStatus } from '@/entities/title';
import { type TitleSearchResult, usersApi } from '@/shared/api';
import { AppSelect } from '@/shared/ui';
import GameSearchModal from '@/features/games/ui/GameSearchModal.vue';
import GameReviewModal from '@/features/games/ui/GameReviewModal.vue';
import UserGameCard from '@/features/games/ui/UserGameCard.vue';
import AvatarCropModal from '@/features/user/ui/AvatarCropModal.vue';


const userStore = useUserStore();
const titleStore = useTitleStore();

const activeTab = ref<TitleCategory>(TitleCategory.GAME);
const activeStatus = ref<UserTitleStatus | 'all'>('all');
const isSearchModalOpen = ref(false);
const isReviewModalOpen = ref(false);
const selectedTitle = ref<TitleSearchResult | null>(null);

const handleTitleSelect = (title: TitleSearchResult) => {
  selectedTitle.value = title;
  selectedInitialData.value = null; // Reset for new entry
  isSearchModalOpen.value = false;
  isReviewModalOpen.value = true;
};

const selectedInitialData = ref<{
  status: UserTitleStatus;
  score: number | null;
  review_text: string | null;
} | null>(null);

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const handleEditTitle = (userTitle: any) => {
  // Map UserTitle to TitleSearchResult
  selectedTitle.value = {
    external_id: userTitle.title.external_id || String(userTitle.title_id), // Fallback if no ext ID
    type: userTitle.title.category,
    title: userTitle.title.name,
    poster_url: userTitle.title.cover_image,
    release_year: userTitle.title.release_year,
    genres: userTitle.title.genres,
  };
  
  selectedInitialData.value = {
    status: userTitle.status,
    score: userTitle.score,
    review_text: userTitle.review_text,
  };
  
  isReviewModalOpen.value = true;
};

const handleTitleAdded = () => {
  titleStore.fetchMyTitles(); // Refresh list
};

const fileInput = ref<HTMLInputElement | null>(null);
const isAvatarModalOpen = ref(false);
const selectedAvatarFile = ref<File | null>(null);

const triggerAvatarUpload = () => {
  fileInput.value?.click();
};

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    selectedAvatarFile.value = target.files[0];
    isAvatarModalOpen.value = true;
    // Reset input so validation triggers again even if same file selected
    target.value = '';
  }
};

const handleAvatarSave = async (blob: Blob) => {
    try {
      // Create a File object from Blob to match API expectaion
      const file = new File([blob], "avatar.jpg", { type: "image/jpeg" });
      const updatedUser = await usersApi.uploadAvatar(file);
      userStore.setUser(updatedUser);
    } catch (e) {
      console.error('Failed to upload avatar', e);
    }
};

// Fetch data on mount
onMounted(() => {
  titleStore.fetchMyTitles();
});

const tabs = [
  { id: TitleCategory.GAME, label: 'Игры' },
  { id: TitleCategory.MOVIE, label: 'Фильмы' },
  { id: TitleCategory.SERIES, label: 'Сериалы' },
  { id: TitleCategory.ANIME, label: 'Аниме' },
] as const;

// Helper to map backend status to display label
const getStatusLabel = (status: UserTitleStatus | 'all', category: TitleCategory) => {
    if (status === 'all') return 'Все';
    
    // Customize labels based on category if needed (e.g., Playing vs Watching)
    if (status === UserTitleStatus.COMPLETED) {
        return category === TitleCategory.GAME ? 'Прошел' : 'Посмотрел';
    }
    if (status === UserTitleStatus.PLAYING) return 'Играю';
    if (status === UserTitleStatus.WATCHING) return 'Смотрю';
    if (status === UserTitleStatus.DROPPED) return 'Дропнул';
    if (status === UserTitleStatus.PLANNED) return 'В планах';
    if (status === UserTitleStatus.ON_HOLD) return 'На паузе';
    return status;
};

// Computed statuses with counts for the current tab
const currentStatuses = computed(() => {
  const category = activeTab.value;
  
  // Define relevant statuses based on category
  const statuses = [
      'all',
      UserTitleStatus.COMPLETED,
      // "Playing" for games, "Watching" for others
      category === TitleCategory.GAME ? UserTitleStatus.PLAYING : UserTitleStatus.WATCHING,
      UserTitleStatus.DROPPED,
      UserTitleStatus.PLANNED,
      UserTitleStatus.ON_HOLD,
  ] as const;

  return statuses.map(status => ({
    id: status,
    label: getStatusLabel(status, category),
    count: titleStore.getCountByStatus(status, category)
  }));
});

// Filtered list of titles to display
const displayedTitles = computed(() => {
    let titles = titleStore.getTitlesByStatus(activeStatus.value, activeTab.value);
    
    if (selectedYear.value) {
        titles = titles.filter(t => {
            const date = t.finished_at ? new Date(t.finished_at) : new Date(t.updated_at); // Fallback to updated_at
            return date.getFullYear() === selectedYear.value;
        });
    }
    
    if (selectedMonth.value !== null) {
        titles = titles.filter(t => {
            const date = t.finished_at ? new Date(t.finished_at) : new Date(t.updated_at);
            return date.getMonth() === selectedMonth.value;
        });
    }
    
    return titles;
});

const selectedYear = ref<number | null>(null);
const selectedMonth = ref<number | null>(null);

const availableYears = computed(() => {
    const years = new Set<number>();
    const titles = titleStore.getTitlesByStatus(activeStatus.value, activeTab.value);
    titles.forEach(t => {
        const date = t.finished_at ? new Date(t.finished_at) : new Date(t.updated_at);
        years.add(date.getFullYear());
    });
    return Array.from(years).sort((a, b) => b - a);
});

const availableYearsOptions = computed(() => {
    return availableYears.value.map(year => ({
        value: year,
        label: String(year)
    }));
});

const monthOptions = computed(() => [
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

watch(activeTab, () => {
  activeStatus.value = 'all';
  selectedYear.value = null; // Reset filters
  selectedMonth.value = null;
});

watch(activeStatus, () => {
    selectedYear.value = null;
    selectedMonth.value = null;
});

const user = computed(() => userStore.user);
const initials = computed(() => {
  const login = user.value?.login || '?';
  return login.substring(0, 1).toUpperCase();
});

const addButtonLabel = computed(() => {
  switch (activeTab.value) {
    case TitleCategory.GAME: return 'Добавить игру';
    case TitleCategory.MOVIE: return 'Добавить фильм';
    case TitleCategory.SERIES: return 'Добавить сериал';
    case TitleCategory.ANIME: return 'Добавить аниме';
    default: return 'Добавить';
  }
});

const activeSearchCategory = computed(() => {
    if (activeTab.value === TitleCategory.SERIES) return 'tv';
    return activeTab.value; // 'game', 'movie', 'anime' match TitleType
});
</script>

<template>
  <div class="max-w-screen-xl mx-auto p-8 flex flex-col gap-7">
    <header class="flex items-center gap-8 p-8 bg-surface border border-border rounded-xl shadow-sm">
      <div 
        class="relative w-[100px] h-[100px] rounded-full group cursor-pointer"
        @click="triggerAvatarUpload"
      >
        <div class="w-full h-full rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-4xl font-bold border-4 border-background shadow-[0_0_0_2px_var(--color-primary-200)] overflow-hidden">
          <img 
            v-if="user?.avatar_url" 
            :src="user.avatar_url" 
            class="w-full h-full object-cover"
            alt="Avatar"
          />
          <span v-else>{{ initials }}</span>
        </div>
        
        <!-- Hover Overlay -->
        <div class="absolute inset-0 rounded-full bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
        </div>

        <input 
          type="file" 
          ref="fileInput" 
          class="hidden" 
          accept="image/*"
          @change="handleFileChange"
        />
      </div>
      
      <div>
        <div class="mb-4 leading-tight">
          <h1 class="text-3xl font-bold text-text m-0">{{ user?.name || user?.login }}</h1>
          <p class="text-base font-medium text-text-secondary">@{{ user?.login }}</p>
        </div>
        
        <div class="flex gap-8">
          <div class="flex flex-col">
            <span class="text-lg font-bold text-text">{{ titleStore.titles.length }}</span>
            <span class="text-sm text-text-muted">Тайтлов</span>
          </div>
          <div class="flex flex-col">
            <span class="text-lg font-bold text-text">0</span>
            <span class="text-sm text-text-muted">Подписки</span>
          </div>
          <div class="flex flex-col">
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

      <div class="flex gap-2 flex-wrap items-center">
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

        <!-- Time Filters -->
        <div class="flex gap-2 ml-auto">
            <AppSelect
                v-model="selectedYear"
                :options="availableYearsOptions"
                placeholder="Все года"
                class="w-32"
            />
            
            <AppSelect
                v-model="selectedMonth"
                :options="monthOptions"
                placeholder="Все месяцы"
                class="w-36"
            />
        </div>
      </div>

      <div class="flex">
        <button
          class="px-4 py-2 bg-primary-500 text-text-dark-1 rounded-lg hover:bg-primary-600 transition-colors font-medium text-sm cursor-pointer"
          @click="isSearchModalOpen = true"
        >
          {{ addButtonLabel }}
        </button>
      </div>
    </div>

    <div v-if="titleStore.isLoading" class="flex justify-center p-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
    </div>

    <div v-else-if="displayedTitles.length > 0" class="flex flex-col gap-4">
      <UserGameCard 
        v-for="userTitle in displayedTitles" 
        :key="userTitle.id"
        :user-title="userTitle"
        :editable="true"
        @edit="handleEditTitle"
      />
    </div>

    <div v-else class="
        flex flex-col items-center justify-center
        py-16 px-8 bg-background-soft rounded-lg
        border border-border text-center
      ">
      <p class="text-xl text-text mb-2">Список тайтлов пуст</p>
      <p class="text-base text-text opacity-70">Здесь будут отображаться ваши тайтлы</p>
    </div>
  </div>
  <GameSearchModal 
    :is-open="isSearchModalOpen" 
    :active-category="activeSearchCategory"
    @close="isSearchModalOpen = false" 
    @select="handleTitleSelect"
  />
  

  
  <GameReviewModal
    :is-open="isReviewModalOpen"
    :title="selectedTitle"
    :initial-data="selectedInitialData"
    @close="isReviewModalOpen = false"
    @added="handleTitleAdded"
  />

  <AvatarCropModal
    :is-open="isAvatarModalOpen"
    :image-file="selectedAvatarFile"
    @close="isAvatarModalOpen = false"
    @save="handleAvatarSave"
  />

  <AvatarCropModal
    :is-open="isAvatarModalOpen"
    :image-file="selectedAvatarFile"
    @close="isAvatarModalOpen = false"
    @save="handleAvatarSave"
  />
</template>
