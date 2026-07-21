<script setup lang="ts">
import { ref, onMounted, computed, watch, type CSSProperties } from 'vue';
import { useRoute } from 'vue-router';
import { apiClient } from '@/shared/api';
import type { UserTitle } from '@/entities/title';
import { usersApi, type User } from '@/shared/api';
import GamePlatformBadge from '@/features/games/ui/GamePlatformBadge.vue';

interface ParsedSegment {
  id: number;
  text: string;
  isSpoiler: boolean;
  isRevealed: boolean;
}

const route = useRoute();
const userTitleId = computed(() => Number(route.params.id));
const entry = ref<UserTitle | null>(null);
const author = ref<User | null>(null);
const isLoading = ref(true);
const parsedReview = ref<ParsedSegment[]>([]);

const parseReviewText = (text: string | null) => {
  if (!text) { parsedReview.value = []; return; }
  const parts = text.split(/(<[^<>]+>)/g);
  parsedReview.value = parts.map((part, index) => {
    if (part.startsWith('<') && part.endsWith('>') && part.length > 2) {
      return { id: index, text: part.slice(1, -1), isSpoiler: true, isRevealed: false };
    }
    return { id: index, text: part, isSpoiler: false, isRevealed: false };
  }).filter(p => p.text.length > 0);
};

const toggleSpoiler = (id: number) => {
  const seg = parsedReview.value.find(s => s.id === id);
  if (seg) seg.isRevealed = !seg.isRevealed;
};

const fetchEntry = async () => {
  isLoading.value = true;
  try {
    entry.value = await apiClient.get<UserTitle>(`/titles/entry/${userTitleId.value}`);
    if (entry.value) {
      author.value = await usersApi.getUser(entry.value.user_id);
    }
  } catch (e) {
    console.error('Failed to fetch review entry', e);
  } finally {
    isLoading.value = false;
    if (entry.value) parseReviewText(entry.value.review_text);
  }
};

onMounted(fetchEntry);

watch(
  () => route.params.id,
  (newId, oldId) => {
    if (newId !== oldId && newId) {
      fetchEntry();
    }
  }
);

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

const categoryLabel = (cat: string) => {
  switch (cat) {
    case 'game': return 'Игра';
    case 'movie': return 'Фильм';
    case 'series': return 'Сериал';
    case 'anime': return 'Аниме';
    default: return cat;
  }
};

const categoryIcon = (cat: string) => {
  switch (cat) {
    case 'game': return '🎮';
    case 'movie': return '🎬';
    case 'series': return '📺';
    case 'anime': return '🎌';
    default: return '📝';
  }
};

const statusLabel = (status: string, category?: string) => {
  switch (status) {
    case 'completed':
      return category === 'game' ? 'Пройдено' : 'Просмотрено';
    case 'playing': 
      return 'Играю';
    case 'watching': 
      return 'Смотрю';
    case 'dropped': 
      return 'Дропнуто';
    case 'planned': 
      return 'В планах';
    case 'on_hold': 
      return 'На паузе';
    default: 
      return status;
  }
};

const interpolateColor = (
  from: [number, number, number],
  to: [number, number, number],
  amount: number,
): [number, number, number] => [
  Math.round(from[0] + (to[0] - from[0]) * amount),
  Math.round(from[1] + (to[1] - from[1]) * amount),
  Math.round(from[2] + (to[2] - from[2]) * amount),
];

const scoreToneRgb = computed<[number, number, number]>(() => {
  const score = entry.value?.score;
  if (!score) return [113, 113, 122];

  const normalizedScore = Math.min(10, Math.max(1, score));
  if (normalizedScore <= 5) {
    return interpolateColor([239, 68, 68], [245, 158, 11], (normalizedScore - 1) / 4);
  }

  return interpolateColor([245, 158, 11], [16, 185, 129], (normalizedScore - 5) / 5);
});

const reviewToneStyle = computed<CSSProperties>(() => ({
  '--review-tone-rgb': scoreToneRgb.value.join(' '),
} as CSSProperties));

const scoreColor = (score: number | null) => score ? 'rgb(var(--review-tone-rgb))' : 'var(--color-text-muted)';

const isCompleted100PercentGame = computed(() =>
  entry.value?.title.category === 'game'
  && entry.value.is_completed_100_percent
);

const formatDate = (dateStr: string | null | undefined) => {
  if (!dateStr) return null;
  const str = new Date(dateStr).toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
  });
  return str.charAt(0).toUpperCase() + str.slice(1);
};
</script>

<template>
  <div class="review-page">
    <!-- Loading -->
    <div v-if="isLoading" class="loading-container">
      <div class="spinner"></div>
    </div>

    <!-- Content -->
    <div v-else-if="entry" class="review-container" :style="reviewToneStyle">
      <!-- Hero section with cover -->
      <div class="review-hero review-accent-card">
        <div class="cover-wrapper" v-if="entry.title.cover_image">
          <img :src="entry.title.cover_image" :alt="entry.title.name" class="cover-img" />
        </div>
        <div class="hero-info">
          <span class="category-badge">
            {{ categoryIcon(entry.title.category) }} {{ categoryLabel(entry.title.category) }}
          </span>
          <h1 class="title-name">{{ entry.title.name }}</h1>
          <div class="meta-row" v-if="entry.title.release_year">
            <span class="meta-year">{{ entry.title.release_year }}</span>
          </div>
          <div class="genres-row" v-if="entry.title.genres && entry.title.genres.length">
            <span v-for="g in entry.title.genres" :key="g" class="genre-tag">{{ g }}</span>
          </div>
        </div>
      </div>

      <!-- Author card -->
      <div class="author-card review-accent-card" v-if="author" @click="$router.push(`/user/${author.id}`)">
        <div class="author-avatar">
          <img v-if="author.avatar_url" :src="author.avatar_url" alt="" class="avatar-img" />
          <span v-else class="avatar-placeholder">{{ author.login.substring(0, 1).toUpperCase() }}</span>
        </div>
        <div class="author-info">
          <span class="author-name">{{ author.name || author.login }}</span>
          <span class="author-login">@{{ author.login }}</span>
        </div>
      </div>

      <!-- Review details -->
      <div class="review-details">
        <div class="detail-cards">
          <div class="detail-card review-accent-card">
            <span class="detail-label">Статус</span>
            <span class="status-value-row">
              <span class="detail-value">{{ statusLabel(entry.status, entry.title.category) }}</span>
              <span
                v-if="isCompleted100PercentGame"
                class="completion-status-badge"
                title="Игра пройдена на 100%"
              >
                100%
              </span>
            </span>
          </div>
          <div class="detail-card review-accent-card score-card" v-if="entry.score">
            <span class="detail-label">Оценка</span>
            <span class="detail-value score" :style="{ color: scoreColor(entry.score) }">
              {{ entry.score }}/10
            </span>
          </div>
          <div class="detail-card review-accent-card" v-if="entry.finished_at">
            <span class="detail-label">Дата завершения</span>
            <span class="detail-value">{{ formatDate(entry.finished_at) }}</span>
          </div>
          <div class="detail-card review-accent-card" v-if="entry.title.category === 'game' && entry.game_platform">
            <span class="detail-label">Платформа</span>
            <GamePlatformBadge
              :platform="entry.game_platform"
              icon-size="lg"
              class="detail-value platform-detail-value"
            />
          </div>
        </div>

        <!-- Review text -->
        <div v-if="entry.review_text" class="review-text-section review-accent-card">
          <h2 class="section-title">Отзыв</h2>
          <div class="review-text">
            <span
              v-for="segment in parsedReview"
              :key="segment.id"
              :class="[
                segment.isSpoiler ? 'spoiler-segment' : '',
                segment.isSpoiler && !segment.isRevealed ? 'spoiler-hidden' : '',
                segment.isSpoiler && segment.isRevealed ? 'spoiler-revealed' : ''
              ]"
              @click="segment.isSpoiler && toggleSpoiler(segment.id)"
              :title="segment.isSpoiler && !segment.isRevealed ? 'Нажмите, чтобы показать спойлер' : ''"
            >{{ segment.text }}</span>
          </div>
        </div>

        <div v-else class="no-review review-accent-card">
          Отзыв не оставлен
        </div>

        <!-- Screenshots gallery -->
        <div v-if="entry.screenshots && entry.screenshots.length > 0" class="screenshots-section review-accent-card">
          <h2 class="section-title">Скриншоты</h2>
          <div class="screenshots-grid">
            <div 
              v-for="(screenshot, idx) in entry.screenshots" 
              :key="screenshot.id"
              class="screenshot-thumb"
              @click="openLightbox(idx)"
            >
              <img :src="screenshot.url" :alt="`Скриншот ${idx + 1}`" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error / not found -->
    <div v-else class="error-container">
      <p>Запись не найдена</p>
      <button @click="$router.back()" class="back-btn">Назад</button>
    </div>
  </div>

  <!-- Lightbox (Teleported to body to avoid z-index issues) -->
  <Teleport to="body">
    <div 
      v-if="lightboxOpen" 
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
          v-if="entry?.screenshots?.[lightboxIndex]" 
          :src="entry.screenshots![lightboxIndex]!.url" 
          class="lightbox-img"
        />
      </div>
      <button 
        v-if="entry?.screenshots && lightboxIndex < entry.screenshots.length - 1" 
        class="lightbox-nav lightbox-next" 
        @click.stop="lightboxIndex++"
      >›</button>
    </div>
  </Teleport>
</template>

<style scoped>
.review-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px 12px 32px;
}

.loading-container {
  display: flex;
  justify-content: center;
  padding: 64px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.review-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

:global(:root),
:global([data-theme="light"]) {
  --review-card-tint: 5%;
  --review-card-tint-strong: 8%;
  --review-card-border: 22%;
  --review-card-shadow: 0.08;
  --review-badge-tint: 10%;
}

:global([data-theme="dark"]) {
  --review-card-tint: 8%;
  --review-card-tint-strong: 12%;
  --review-card-border: 28%;
  --review-card-shadow: 0.18;
  --review-badge-tint: 14%;
}

:global([data-theme="midnight"]) {
  --review-card-tint: 10%;
  --review-card-tint-strong: 14%;
  --review-card-border: 32%;
  --review-card-shadow: 0.2;
  --review-badge-tint: 16%;
}

.review-accent-card {
  background:
    linear-gradient(135deg, rgb(var(--review-tone-rgb) / var(--review-card-overlay, 0.08)), transparent 58%),
    color-mix(in srgb, rgb(var(--review-tone-rgb)) var(--review-card-tint), var(--color-background-soft));
  border: 1px solid color-mix(in srgb, rgb(var(--review-tone-rgb)) var(--review-card-border), var(--color-border));
  box-shadow: 0 12px 32px rgb(var(--review-tone-rgb) / var(--review-card-shadow));
  transition:
    background 450ms ease,
    background-color 450ms ease,
    border-color 450ms ease,
    box-shadow 450ms ease,
    color 250ms ease;
}

/* Hero */
.review-hero {
  display: flex;
  gap: 24px;
  padding: 24px;
  border-radius: 16px;
  --review-card-overlay: 0.1;
}

.cover-wrapper {
  flex-shrink: 0;
  width: 160px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}

.cover-img {
  width: 100%;
  height: auto;
  display: block;
}

.hero-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
}

.category-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: rgb(var(--review-tone-rgb));
  background: color-mix(in srgb, rgb(var(--review-tone-rgb)) var(--review-badge-tint), var(--color-surface-hover));
  padding: 4px 10px;
  border-radius: 6px;
  width: fit-content;
  transition: background-color 450ms ease, color 450ms ease;
}

.title-name {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
  line-height: 1.2;
}

.meta-year {
  color: var(--color-text-secondary);
  font-size: 15px;
}

.genres-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.genre-tag {
  font-size: 12px;
  padding: 3px 8px;
  background: color-mix(in srgb, rgb(var(--review-tone-rgb)) var(--review-badge-tint), transparent);
  color: rgb(var(--review-tone-rgb));
  border-radius: 4px;
  transition: background-color 450ms ease, color 450ms ease;
}

/* Author */
.author-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  cursor: pointer;
  --review-card-overlay: 0.05;
}

.author-card:hover {
  border-color: rgb(var(--review-tone-rgb));
}

.author-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
  background: color-mix(in srgb, rgb(var(--review-tone-rgb)) 42%, var(--color-surface-hover));
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background-color 450ms ease;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-size: 18px;
  font-weight: 700;
  color: white;
}

.author-info {
  display: flex;
  flex-direction: column;
}

.author-name {
  font-weight: 600;
  color: var(--color-text);
  font-size: 15px;
}

.author-login {
  font-size: 13px;
  color: var(--color-text-muted);
}

/* Details */
.review-details {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-cards {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.detail-card {
  flex: 1;
  min-width: 120px;
  padding: 16px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  --review-card-overlay: 0.05;
}

.detail-card.score-card {
  --review-card-tint: var(--review-card-tint-strong);
  --review-card-overlay: 0.1;
}

.detail-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--color-text-muted);
  font-weight: 500;
}

.detail-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
}

.platform-detail-value {
  align-items: center;
  line-height: 1;
  margin-top: 4px;
}

.detail-value.score {
  font-size: 24px;
}

.status-value-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.completion-status-badge {
  flex-shrink: 0;
  padding: 3px 8px;
  border-radius: 9999px;
  color: white;
  font-size: 12px;
  font-weight: 800;
  background: linear-gradient(135deg, rgb(124 58 237 / 0.95), rgb(217 70 239 / 0.95));
  border: 1px solid rgb(168 85 247 / 0.55);
  box-shadow: 0 8px 18px rgb(168 85 247 / 0.24);
}

/* Review text */
.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 12px;
}

.review-text-section {
  padding: 20px;
  border-radius: 12px;
  --review-card-overlay: 0.04;
}

.review-text {
  font-size: 15px;
  line-height: 1.7;
  color: var(--color-text);
  white-space: pre-wrap;
}

.spoiler-segment {
  cursor: pointer;
  transition: all 0.2s;
  padding: 1px 3px;
  border-radius: 4px;
  margin: 0 1px;
}

.spoiler-hidden {
  background: #3f3f46;
  color: transparent;
  filter: blur(4px);
  user-select: none;
}

.spoiler-hidden:hover {
  background: #52525b;
}

.spoiler-revealed {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-text);
}

.no-review {
  padding: 32px;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 14px;
  border-radius: 12px;
  --review-card-overlay: 0.04;
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 64px;
  color: var(--color-text-muted);
}

.back-btn {
  padding: 8px 20px;
  background: var(--color-primary-500);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: opacity 0.2s;
  min-height: 44px;
}

.back-btn:hover {
  opacity: 0.9;
}

@media (max-width: 640px) {
  .review-hero {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 16px;
    padding: 16px;
  }

  .hero-info {
    align-items: center;
  }

  .cover-wrapper {
    width: 120px;
  }

  .title-name {
    font-size: 22px;
  }

  .detail-cards {
    flex-direction: column;
  }

  .review-text-section,
  .screenshots-section {
    padding: 16px;
  }

  .error-container {
    padding: 48px 16px;
    text-align: center;
  }
}

/* Screenshots */
.screenshots-section {
  padding: 20px;
  margin-top: 8px;
  border-radius: 12px;
  --review-card-overlay: 0.04;
}

.screenshots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px;
}

.screenshot-thumb {
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  aspect-ratio: 16/9;
  background: var(--color-surface-hover);
  transition: transform 0.2s, box-shadow 0.2s;
}

.screenshot-thumb:hover {
  transform: scale(1.03);
  box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}

.screenshot-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* Lightbox */
.lightbox-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(0,0,0,0.9);
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
  background: rgba(255,255,255,0.1);
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
  background: rgba(255,255,255,0.2);
}

.lightbox-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255,255,255,0.1);
  border: none;
  color: white;
  font-size: 32px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  z-index: 101;
}

.lightbox-nav:hover {
  background: rgba(255,255,255,0.2);
}

.lightbox-prev {
  left: 16px;
}

.lightbox-next {
  right: 16px;
}

.lightbox-content {
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox-img {
  max-width: 100%;
  max-height: 90vh;
  object-fit: contain;
  border-radius: 8px;
}

@media (max-width: 640px) {
  .lightbox-close {
    top: max(12px, env(safe-area-inset-top));
    right: 12px;
  }

  .lightbox-nav {
    top: auto;
    bottom: max(16px, env(safe-area-inset-bottom));
    transform: none;
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
    max-height: calc(100dvh - 150px);
  }
}

@media (min-width: 641px) {
  .review-page {
    padding-top: 32px;
  }
}
</style>
