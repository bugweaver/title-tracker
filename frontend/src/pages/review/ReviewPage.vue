<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { apiClient } from '@/shared/api';
import type { UserTitle } from '@/entities/title';
import { usersApi, type User } from '@/shared/api';

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

const statusLabel = (status: string) => {
  switch (status) {
    case 'completed': return 'Пройдено';
    case 'playing': return 'Играю';
    case 'watching': return 'Смотрю';
    case 'dropped': return 'Дропнуто';
    case 'planned': return 'В планах';
    case 'on_hold': return 'На паузе';
    default: return status;
  }
};

const scoreColor = (score: number | null) => {
  if (!score) return 'var(--color-text-muted)';
  if (score >= 8) return '#22c55e';
  if (score >= 6) return '#eab308';
  if (score >= 4) return '#f97316';
  return '#ef4444';
};

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
    <div v-else-if="entry" class="review-container">
      <!-- Hero section with cover -->
      <div class="review-hero">
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
      <div class="author-card" v-if="author" @click="$router.push(`/user/${author.id}`)">
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
          <div class="detail-card">
            <span class="detail-label">Статус</span>
            <span class="detail-value">{{ statusLabel(entry.status) }}</span>
          </div>
          <div class="detail-card" v-if="entry.score">
            <span class="detail-label">Оценка</span>
            <span class="detail-value score" :style="{ color: scoreColor(entry.score) }">
              {{ entry.score }}/10
            </span>
          </div>
          <div class="detail-card" v-if="entry.finished_at">
            <span class="detail-label">Дата завершения</span>
            <span class="detail-value">{{ formatDate(entry.finished_at) }}</span>
          </div>
        </div>

        <!-- Review text -->
        <div v-if="entry.review_text" class="review-text-section">
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

        <div v-else class="no-review">
          Отзыв не оставлен
        </div>
      </div>
    </div>

    <!-- Error / not found -->
    <div v-else class="error-container">
      <p>Запись не найдена</p>
      <button @click="$router.back()" class="back-btn">Назад</button>
    </div>
  </div>
</template>

<style scoped>
.review-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 16px;
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

/* Hero */
.review-hero {
  display: flex;
  gap: 24px;
  padding: 24px;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 16px;
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
  color: var(--color-text-muted);
  background: var(--color-surface-hover);
  padding: 4px 10px;
  border-radius: 6px;
  width: fit-content;
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
  background: var(--color-primary-500-10, rgba(99,102,241,0.1));
  color: var(--color-primary-500);
  border-radius: 4px;
}

/* Author */
.author-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.author-card:hover {
  border-color: var(--color-primary-500);
}

.author-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--color-primary-100);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-primary-600);
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
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
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

.detail-value.score {
  font-size: 24px;
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
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 12px;
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
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 12px;
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
}

.back-btn:hover {
  opacity: 0.9;
}

@media (max-width: 640px) {
  .review-hero {
    flex-direction: column;
    align-items: center;
    text-align: center;
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
}
</style>
