<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted, type CSSProperties } from 'vue';
import { useRouter } from 'vue-router';
import { type GamePlatform, type UserTitleStatus, type Screenshot } from '@/entities/title';
import { TitleCategory } from '@/entities/title';
import GamePlatformBadge from './GamePlatformBadge.vue';

interface Title {
  id: number;
  name: string;
  category: TitleCategory;
  cover_image: string | null;
  release_year: number | null;
  genres: string[] | null;
}

interface UserTitle {
  id: number;
  user_id: number;
  title_id: number;
  status: UserTitleStatus;
  score: number | null;
  review_text: string | null;
  is_spoiler?: boolean;
  is_completed_100_percent: boolean;
  game_platform: GamePlatform | null;
  title: Title;
  finished_at?: string | null;
  screenshots?: Screenshot[];
}

const props = withDefaults(defineProps<{
  userTitle: UserTitle;
  editable?: boolean;
}>(), {
  editable: false
});

defineEmits<{
  (e: 'edit', userTitle: UserTitle): void;
}>();

const score = computed(() => {
  if (props.userTitle.score === null) return null;
  return props.userTitle.score === 10 ? '10' : props.userTitle.score.toFixed(1);
});

const interpolateColor = (
  from: [number, number, number],
  to: [number, number, number],
  amount: number,
): [number, number, number] => [
  Math.round(from[0] + (to[0] - from[0]) * amount),
  Math.round(from[1] + (to[1] - from[1]) * amount),
  Math.round(from[2] + (to[2] - from[2]) * amount),
];

const cardToneRgb = computed<[number, number, number]>(() => {
  const scoreValue = props.userTitle.score;
  if (!scoreValue) {
    if (props.userTitle.status === 'playing' || props.userTitle.status === 'watching') {
      return [59, 130, 246];
    }
    if (props.userTitle.status === 'on_hold') {
      return [249, 115, 22];
    }
    return [113, 113, 122];
  }

  const normalizedScore = Math.min(10, Math.max(1, scoreValue));
  if (normalizedScore <= 5) {
    return interpolateColor([239, 68, 68], [245, 158, 11], (normalizedScore - 1) / 4);
  }

  return interpolateColor([245, 158, 11], [16, 185, 129], (normalizedScore - 5) / 5);
});

const cardToneStyle = computed<CSSProperties>(() => ({
  '--card-tone-rgb': cardToneRgb.value.join(' '),
} as CSSProperties));

const statusLabel = computed(() => {
    // Basic mapping, can be moved to shared helper if needed
    const s = props.userTitle.status;
    const cat = props.userTitle.title.category;
    if (s === 'completed') return cat === 'game' ? 'Прошел' : 'Посмотрел';
    if (s === 'playing') return cat === 'game' ? 'Играю' : 'Смотрю';
    if (s === 'watching') return 'Смотрю';
    if (s === 'dropped') return 'Дропнул';
    if (s === 'planned') return 'В планах';
    if (s === 'on_hold') return 'На паузе';
    return s;
});

const statusColorClass = computed(() => {
    const s = props.userTitle.status;
    if (s === 'completed') return 'bg-emerald-100 text-emerald-700';
    if (s === 'playing' || s === 'watching') return 'bg-blue-100 text-blue-700';
    if (s === 'on_hold') return 'bg-amber-100 text-amber-700';
    if (s === 'planned') return 'bg-slate-100 text-slate-700';
    if (s === 'dropped') return 'bg-red-100 text-red-700';
    return 'bg-gray-100 text-gray-700';
});

const isCompleted100PercentGame = computed(() =>
  props.userTitle.title.category === TitleCategory.GAME
  && props.userTitle.is_completed_100_percent
);

const gamePlatform = computed(() =>
  props.userTitle.title.category === TitleCategory.GAME
    ? props.userTitle.game_platform
    : null
);

const isRevealed = ref(false);
const isExpanded = ref(false);
const shouldShowReadMore = computed(() => {
    return (props.userTitle.review_text?.length || 0) > 300;
});

interface ParsedSegment {
    id: number;
    text: string;
    isSpoiler: boolean;
    isRevealed: boolean;
}

const parsedReview = ref<ParsedSegment[]>([]);

// Re-parse when review text changes
watch(() => props.userTitle.review_text, (newText: string | null) => {
    if (!newText) {
        parsedReview.value = [];
        return;
    }
    
    const parts = newText.split(/(<[^<>]+>)/g);
    parsedReview.value = parts.map((part: string, index: number) => {
        if (part.startsWith('<') && part.endsWith('>') && part.length > 2) {
            return {
                id: index,
                text: part.slice(1, -1),
                isSpoiler: true,
                isRevealed: false
            };
        }
        return {
            id: index,
            text: part,
            isSpoiler: false,
            isRevealed: false
        };
    }).filter((part: ParsedSegment) => part.text.length > 0);
}, { immediate: true });

const toggleSpoiler = (id: number) => {
    const segment = parsedReview.value.find(s => s.id === id);
    if (segment) {
        segment.isRevealed = !segment.isRevealed;
    }
};

const router = useRouter();

const goToReview = () => {
  router.push(`/review/${props.userTitle.id}`);
};

// Lightbox
const lightboxOpen = ref(false);
const lightboxIndex = ref(0);

const openLightbox = (idx: number) => {
  lightboxIndex.value = idx;
  lightboxOpen.value = true;
};

const closeLightbox = () => {
  lightboxOpen.value = false;
};

const onLightboxKeydown = (e: KeyboardEvent) => {
  if (!lightboxOpen.value) return;
  const screenshots = props.userTitle.screenshots;
  if (!screenshots) return;
  if (e.key === 'Escape') closeLightbox();
  if (e.key === 'ArrowRight' && lightboxIndex.value < screenshots.length - 1) lightboxIndex.value++;
  if (e.key === 'ArrowLeft' && lightboxIndex.value > 0) lightboxIndex.value--;
};
onMounted(() => window.addEventListener('keydown', onLightboxKeydown));
onUnmounted(() => window.removeEventListener('keydown', onLightboxKeydown));
</script>

<template>
  <div 
    class="game-card flex cursor-pointer flex-col gap-4 rounded-xl p-4 sm:flex-row sm:gap-5 sm:p-5"
    :style="cardToneStyle"
    @click="goToReview"
  >
    <!-- Poster -->
    <div class="group relative h-36 w-24 shrink-0 self-center overflow-hidden rounded-lg bg-[var(--color-bg-tertiary)] shadow-sm sm:h-44 sm:w-32 sm:self-auto">
      <img 
        v-if="userTitle.title.cover_image" 
        :src="userTitle.title.cover_image" 
        :alt="userTitle.title.name"
        class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-[var(--color-text-tertiary)] text-xs text-center p-2">
        No Image
      </div>
    </div>
    
    <!-- Content -->
    <div class="flex min-w-0 flex-grow flex-col justify-center py-1">
      
      <!-- Top Row: Badge & Status -->
      <div class="mb-2 flex flex-wrap items-center gap-2 sm:gap-3">
        <span 
          v-if="score"
          class="score-badge px-2.5 py-1 rounded-md font-bold text-sm"
        >
          ★ {{ score }}
        </span>
        
        <span 
          class="text-xs px-2.5 py-1 rounded-full font-medium"
          :class="statusColorClass"
        >
          {{ statusLabel }}
        </span>

        <span
          v-if="isCompleted100PercentGame"
          class="completion-badge text-xs px-2.5 py-1 rounded-full font-black"
          title="Игра пройдена на 100%"
        >
          100% пройдено
        </span>

        <GamePlatformBadge
          v-if="gamePlatform"
          :platform="gamePlatform"
          icon-size="lg"
          class="platform-badge text-xs px-2.5 py-1 rounded-full font-semibold"
        />
        
        <button 
          v-if="editable"
          class="ml-auto flex h-11 w-11 items-center justify-center rounded-full text-[var(--color-text-tertiary)] transition-colors hover:bg-[var(--color-bg-tertiary)] hover:text-[var(--color-primary-500)]"
          @click.stop="$emit('edit', userTitle)"
          title="Редактировать"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
        </button>
      </div>

      <!-- Title -->
      <h3 class="mb-2 line-clamp-2 break-words text-xl font-extrabold leading-tight text-[var(--color-text-primary)] sm:text-2xl">
        {{ userTitle.title.name }}
      </h3>
      
      <!-- Meta -->
      <div class="text-sm text-[var(--color-text-secondary)] font-medium" style="margin-bottom: 5px;">
        <span v-if="userTitle.title.release_year">{{ userTitle.title.release_year }}</span>
        <span v-if="userTitle.title.release_year && userTitle.title.genres?.length" class="mx-1.5">•</span>
        <span v-if="userTitle.title.genres?.length" class="opacity-80">
            {{ userTitle.title.genres.slice(0, 3).join(', ') }}
        </span>
      </div>

      <!-- Review -->
      <!-- Review -->
      <div v-if="userTitle.review_text" class="text-sm text-[var(--color-text-secondary)] max-w-2xl">
        <div 
          class="leading-relaxed opacity-90 transition-all duration-300 break-words whitespace-pre-wrap"
          :class="{ 'line-clamp-3': !isExpanded && !isRevealed }" 
        >
          <span 
            v-for="segment in parsedReview" 
            :key="segment.id"
            :class="[
              segment.isSpoiler ? 'cursor-pointer transition-all duration-200 py-0.5 px-1 rounded mx-0.5 select-none' : '',
              segment.isSpoiler && !segment.isRevealed ? 'spoiler-hidden' : '',
              segment.isSpoiler && segment.isRevealed ? 'spoiler-revealed' : ''
            ]"
            @click.stop="segment.isSpoiler && toggleSpoiler(segment.id)"
            :title="segment.isSpoiler && !segment.isRevealed ? 'Нажмите, чтобы показать спойлер' : ''"
          >{{ segment.text }}</span>
        </div>
        
        <button 
          v-if="shouldShowReadMore" 
          @click.stop="isExpanded = !isExpanded" 
          class="mt-1 inline-flex min-h-11 cursor-pointer items-center text-sm font-medium text-primary-500 hover:text-primary-600 hover:underline"
        >
          {{ isExpanded ? 'Свернуть' : 'Читать далее' }}
        </button>
      </div>

      <!-- Screenshots thumbnails -->
      <div v-if="userTitle.screenshots && userTitle.screenshots.length > 0" class="flex max-w-full gap-1.5 overflow-x-auto pb-1" style="margin-top: 16px;" @click.stop>
        <div 
          v-for="(screenshot, idx) in userTitle.screenshots.slice(0, 4)" 
          :key="screenshot.id"
          class="screenshot-chip w-16 h-12 rounded-md overflow-hidden flex-shrink-0 relative cursor-pointer hover:ring-2 transition-all"
          @click="openLightbox(idx)"
        >
          <img :src="screenshot.url" class="w-full h-full object-cover" />
          <div 
            v-if="idx === 3 && userTitle.screenshots.length > 4" 
            class="absolute inset-0 bg-black/60 flex items-center justify-center text-white text-xs font-bold"
          >+{{ userTitle.screenshots.length - 4 }}</div>
        </div>
      </div>

    </div>
  </div>

  <!-- Lightbox -->
  <Teleport to="body">
    <div 
      v-if="lightboxOpen && userTitle.screenshots" 
      class="lightbox-overlay"
      @click="closeLightbox"
    >
      <button class="lightbox-close" @click.stop="closeLightbox">✕</button>
      <button 
        v-if="lightboxIndex > 0" 
        class="lightbox-nav lightbox-prev" 
        @click.stop="lightboxIndex--"
      >‹</button>
      <div class="lightbox-content" @click.stop>
        <img 
          v-if="userTitle.screenshots[lightboxIndex]" 
          :src="userTitle.screenshots[lightboxIndex]!.url" 
          class="lightbox-img"
        />
        <div class="lightbox-counter">{{ lightboxIndex + 1 }} / {{ userTitle.screenshots.length }}</div>
      </div>
      <button 
        v-if="lightboxIndex < userTitle.screenshots.length - 1" 
        class="lightbox-nav lightbox-next" 
        @click.stop="lightboxIndex++"
      >›</button>
    </div>
  </Teleport>
</template>

<style scoped>
:global(:root),
:global([data-theme="light"]) {
  --game-card-tint: 5%;
  --game-card-overlay: 0.08;
  --game-card-border: 24%;
  --game-card-shadow: 0.08;
  --game-card-badge-tint: 10%;
  --completion-badge-text: white;
  --completion-badge-border: 0.45;
  --completion-badge-shadow: 0.24;
}

:global([data-theme="dark"]) {
  --game-card-tint: 8%;
  --game-card-overlay: 0.12;
  --game-card-border: 30%;
  --game-card-shadow: 0.16;
  --game-card-badge-tint: 14%;
  --completion-badge-text: #0f172a;
  --completion-badge-border: 0.55;
  --completion-badge-shadow: 0.28;
}

:global([data-theme="midnight"]) {
  --game-card-tint: 10%;
  --game-card-overlay: 0.14;
  --game-card-border: 34%;
  --game-card-shadow: 0.18;
  --game-card-badge-tint: 16%;
  --completion-badge-text: #0f172a;
  --completion-badge-border: 0.6;
  --completion-badge-shadow: 0.3;
}

.game-card {
  background:
    linear-gradient(135deg, rgb(var(--card-tone-rgb) / var(--game-card-overlay)), transparent 58%),
    color-mix(in srgb, rgb(var(--card-tone-rgb)) var(--game-card-tint), var(--color-background-soft));
  border: 1px solid color-mix(in srgb, rgb(var(--card-tone-rgb)) var(--game-card-border), var(--color-border));
  box-shadow: 0 12px 32px rgb(var(--card-tone-rgb) / var(--game-card-shadow));
  transition:
    background 450ms ease,
    border-color 450ms ease,
    box-shadow 450ms ease,
    transform 250ms ease;
}

.game-card:hover {
  border-color: rgb(var(--card-tone-rgb));
  box-shadow: 0 16px 40px rgb(var(--card-tone-rgb) / calc(var(--game-card-shadow) + 0.08));
}

.score-badge {
  color: rgb(var(--card-tone-rgb));
  background: color-mix(in srgb, rgb(var(--card-tone-rgb)) var(--game-card-badge-tint), var(--color-surface-hover));
  border: 1px solid color-mix(in srgb, rgb(var(--card-tone-rgb)) 34%, var(--color-border));
  transition: background-color 450ms ease, border-color 450ms ease, color 450ms ease;
}

.completion-badge {
  color: var(--completion-badge-text);
  background:
    linear-gradient(135deg, rgb(124 58 237 / 0.95), rgb(217 70 239 / 0.95));
  border: 1px solid rgb(168 85 247 / var(--completion-badge-border));
  box-shadow: 0 8px 18px rgb(168 85 247 / var(--completion-badge-shadow));
}

.platform-badge {
  color: rgb(var(--card-tone-rgb));
  background: color-mix(in srgb, rgb(var(--card-tone-rgb)) var(--game-card-badge-tint), var(--color-surface-hover));
  border: 1px solid color-mix(in srgb, rgb(var(--card-tone-rgb)) 28%, var(--color-border));
}

.screenshot-chip {
  background: color-mix(in srgb, rgb(var(--card-tone-rgb)) var(--game-card-badge-tint), var(--color-surface-hover));
}

.screenshot-chip:hover {
  --tw-ring-color: rgb(var(--card-tone-rgb));
}

.spoiler-hidden {
  background: #3f3f46;
  color: transparent;
  filter: blur(4px);
  border-radius: 4px;
  transition: all 0.2s;
}
.spoiler-hidden:hover {
  background: #52525b;
}
.spoiler-revealed {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-text-primary);
  transition: all 0.2s;
}

/* Lightbox */
.lightbox-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(0, 0, 0, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  z-index: 101;
}

.lightbox-close:hover {
  background: rgba(255, 255, 255, 0.25);
}

.lightbox-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  font-size: 36px;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  z-index: 101;
  user-select: none;
}

.lightbox-nav:hover {
  background: rgba(255, 255, 255, 0.25);
}

.lightbox-prev {
  left: 20px;
}

.lightbox-next {
  right: 20px;
}

.lightbox-content {
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.lightbox-img {
  max-width: 100%;
  max-height: 85vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.lightbox-counter {
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
  font-weight: 500;
}

@media (max-width: 639px) {
  .lightbox-close {
    top: max(12px, env(safe-area-inset-top));
    right: 12px;
  }

  .lightbox-nav {
    top: auto;
    bottom: max(16px, env(safe-area-inset-bottom));
    width: 48px;
    height: 48px;
  }

  .lightbox-prev {
    left: calc(50% - 58px);
  }

  .lightbox-next {
    right: calc(50% - 58px);
  }

  .lightbox-content {
    max-width: calc(100vw - 24px);
    max-height: calc(100dvh - 120px);
  }

  .lightbox-img {
    max-height: calc(100dvh - 160px);
  }
}
</style>

