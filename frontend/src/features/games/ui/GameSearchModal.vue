<script setup lang="ts">
import { ref, watch, computed } from 'vue';
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

// Set active tab from prop when opening
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
     if (props.activeCategory && ['game', 'movie', 'tv', 'anime'].includes(props.activeCategory)) {
        activeTab.value = props.activeCategory as TitleType;
     } else {
        activeTab.value = 'game';
     }
     // Clear previous results when opening
     results.value = [];
     searchQuery.value = '';
  }
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
<div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click="handleClose">
    <div class="w-full max-w-2xl bg-zinc-900 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]" @click.stop>
      <!-- Header -->
      <div class="p-4 border-b border-zinc-800 flex items-center justify-between">
        <h2 class="text-xl font-bold text-white">
          Добавить {{ getTitleLabel }}
        </h2>
        <button @click="handleClose" class="text-zinc-400 hover:text-white">
          ✕
        </button>
      </div>

      <!-- Tabs -->
      <div class="flex border-b border-zinc-800">
        <button 
          class="flex-1 py-3 text-sm font-medium transition-colors border-b-2"
          :class="activeTab === 'game' ? 'border-primary-500 text-white' : 'border-transparent text-zinc-400 hover:text-white'"
          @click="activeTab = 'game'"
        >
          Games
        </button>
        <button 
          class="flex-1 py-3 text-sm font-medium transition-colors border-b-2"
          :class="activeTab === 'movie' ? 'border-primary-500 text-white' : 'border-transparent text-zinc-400 hover:text-white'"
          @click="activeTab = 'movie'"
        >
          Movies
        </button>
        <button 
          class="flex-1 py-3 text-sm font-medium transition-colors border-b-2"
          :class="activeTab === 'tv' ? 'border-primary-500 text-white' : 'border-transparent text-zinc-400 hover:text-white'"
          @click="activeTab = 'tv'"
        >
          TV Shows
        </button>
        <button 
          class="flex-1 py-3 text-sm font-medium transition-colors border-b-2"
          :class="activeTab === 'anime' ? 'border-primary-500 text-white' : 'border-transparent text-zinc-400 hover:text-white'"
          @click="activeTab = 'anime'"
        >
          Anime
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
      <div class="flex-1 overflow-y-auto p-4 space-y-2 min-h-[300px]">
        <div v-if="isLoading" class="text-center py-8 text-zinc-400">
          Searching...
        </div>
        
        <div v-else-if="results.length === 0 && searchQuery" class="text-center py-8 text-zinc-400">
          No titles found.
        </div>

        <div 
          v-for="title in results" 
          :key="title.external_id + title.type" 
          class="flex items-center gap-4 p-3 rounded-lg hover:bg-zinc-800 transition-colors group"
        >
          <!-- Cover -->
          <div class="w-12 h-16 bg-zinc-800 rounded overflow-hidden flex-shrink-0">
            <img 
              v-if="title.poster_url" 
              :src="title.poster_url" 
              :alt="title.title" 
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-zinc-600 text-xs">
              No Img
            </div>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-baseline gap-2">
              <h3 class="font-bold text-white truncate">{{ title.title }}</h3>
              <span v-if="title.release_year" class="text-xs text-zinc-400">
                {{ title.release_year }}
              </span>
            </div>
            <div class="text-xs text-zinc-400 truncate">
               {{ title.original_title }}
            </div>
          </div>

          <!-- Action -->
          <AppButton 
            variant="ghost" 
            size="sm"
            class="opacity-0 group-hover:opacity-100 transition-opacity"
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
