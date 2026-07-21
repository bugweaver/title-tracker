<script setup lang="ts">
import { ref, watch, computed, onUnmounted } from 'vue';
import { useTheme } from '@/shared/composables';
import AppInput from '@/shared/ui/AppInput.vue';
import AppButton from '@/shared/ui/AppButton.vue';
import { titlesApi, type TitleSearchResult, type TitleType } from '@/shared/api/titles';
import { Plus } from "lucide-vue-next"

const props = defineProps<{
  isOpen: boolean;
  activeCategory?: string; // 'game', 'movie', etc.
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'select', title: TitleSearchResult): void;
}>();

useTheme();
const searchQuery = ref('');
const results = ref<TitleSearchResult[]>([]);
const isLoading = ref(false);
const activeTab = ref<TitleType>('game');
let previousBodyOverflow = '';

// Set active tab from prop when opening
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
     previousBodyOverflow = document.body.style.overflow;
     document.body.style.overflow = 'hidden';
     if (props.activeCategory && ['game', 'movie', 'tv', 'anime'].includes(props.activeCategory)) {
        activeTab.value = props.activeCategory as TitleType;
     } else {
        activeTab.value = 'game';
     }
     // Clear previous results when opening
     results.value = [];
     searchQuery.value = '';
  } else {
     document.body.style.overflow = previousBodyOverflow;
  }
});

onUnmounted(() => {
  document.body.style.overflow = previousBodyOverflow;
});

// Clear results when tab changes
watch(activeTab, () => {
  results.value = [];
  if (searchQuery.value) {
    searchTitles();
  }
});

let debounceTimeout: number | undefined;

const searchTitles = async () => {
  if (!searchQuery.value.trim()) {
    results.value = [];
    return;
  }

  isLoading.value = true;
  try {
    results.value = await titlesApi.search(searchQuery.value, activeTab.value);
  } catch (error) {
    console.error('Failed to search titles:', error);
  } finally {
    isLoading.value = false;
  }
};

watch(searchQuery, () => {
  clearTimeout(debounceTimeout);
  debounceTimeout = window.setTimeout(searchTitles, 500);
});

const handleClose = () => {
  searchQuery.value = '';
  results.value = [];
  emit('close');
};

const getTitleLabel = computed(() => {
    switch(activeTab.value) {
        case 'game': return 'игру';
        case 'movie': return 'фильм';
        case 'tv': return 'сериал';
        case 'anime': return 'аниме';
        default: return 'тайтл';
    }
});
</script>

<template>
<div v-if="isOpen" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm sm:p-4" @click="handleClose">
    <div class="flex h-[100dvh] w-full max-w-2xl flex-col overflow-hidden bg-surface shadow-2xl sm:h-auto sm:max-h-[85dvh] sm:rounded-xl sm:border sm:border-border" @click.stop>
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-border px-4 pb-4 pt-[calc(1rem+env(safe-area-inset-top))] sm:p-4">
        <h2 class="text-lg font-bold text-text sm:text-xl">
          Добавить {{ getTitleLabel }}
        </h2>
        <button @click="handleClose" class="flex h-11 w-11 items-center justify-center rounded-lg text-xl text-text-secondary hover:bg-surface-hover hover:text-text" aria-label="Закрыть">
          ✕
        </button>
      </div>

      <!-- Tabs -->
      <div class="flex shrink-0 overflow-x-auto border-b border-border [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        <button 
          class="min-h-11 min-w-24 flex-1 shrink-0 border-b-2 px-4 py-3 text-sm font-medium transition-colors"
          :class="activeTab === 'game' ? 'border-primary-500 text-text' : 'border-transparent text-text-secondary hover:text-text'"
          @click="activeTab = 'game'"
        >
          Игры
        </button>
        <button 
          class="min-h-11 min-w-24 flex-1 shrink-0 border-b-2 px-4 py-3 text-sm font-medium transition-colors"
          :class="activeTab === 'movie' ? 'border-primary-500 text-text' : 'border-transparent text-text-secondary hover:text-text'"
          @click="activeTab = 'movie'"
        >
          Фильмы
        </button>
        <button 
          class="min-h-11 min-w-24 flex-1 shrink-0 border-b-2 px-4 py-3 text-sm font-medium transition-colors"
          :class="activeTab === 'tv' ? 'border-primary-500 text-text' : 'border-transparent text-text-secondary hover:text-text'"
          @click="activeTab = 'tv'"
        >
          Сериалы
        </button>
        <button 
          class="min-h-11 min-w-24 flex-1 shrink-0 border-b-2 px-4 py-3 text-sm font-medium transition-colors"
          :class="activeTab === 'anime' ? 'border-primary-500 text-text' : 'border-transparent text-text-secondary hover:text-text'"
          @click="activeTab = 'anime'"
        >
          Аниме
        </button>
      </div>

      <!-- Search -->
      <div class="p-4">
        <AppInput 
          v-model="searchQuery" 
          placeholder="Search..." 
          autofocus
        />
      </div>

      <!-- Results -->
      <div class="min-h-0 flex-1 space-y-2 overflow-y-auto p-3 pb-[calc(1rem+env(safe-area-inset-bottom))] sm:min-h-[300px] sm:p-4">
        <div v-if="isLoading" class="py-8 text-center text-text-muted">
          Searching...
        </div>
        
        <div v-else-if="results.length === 0 && searchQuery" class="py-8 text-center text-text-muted">
          No titles found.
        </div>

        <div 
          v-for="title in results" 
          :key="title.external_id + title.type" 
          class="group flex items-center gap-3 rounded-lg p-2 transition-colors hover:bg-surface-hover sm:gap-4 sm:p-3"
        >
          <!-- Cover -->
          <div class="h-16 w-12 flex-shrink-0 overflow-hidden rounded bg-background-mute">
            <img 
              v-if="title.poster_url" 
              :src="title.poster_url" 
              :alt="title.title" 
              class="w-full h-full object-cover"
            />
            <div v-else class="flex h-full w-full items-center justify-center text-xs text-text-muted">
              No Img
            </div>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-baseline gap-2">
              <h3 class="truncate font-bold text-text">{{ title.title }}</h3>
              <span v-if="title.release_year" class="shrink-0 text-xs text-text-muted">
                {{ title.release_year }}
              </span>
            </div>
            <div class="truncate text-xs text-text-muted">
               {{ title.original_title }}
            </div>
          </div>

          <!-- Action -->
          <AppButton 
            variant="ghost" 
            size="sm"
            class="shrink-0 opacity-100 transition-opacity md:opacity-0 md:group-hover:opacity-100"
            title="Добавить"
            @click="$emit('select', title)"
          >
            <span class="text-2xl leading-none"><Plus /></span>
          </AppButton>
        </div>
      </div>
    </div>
  </div>
</template>
