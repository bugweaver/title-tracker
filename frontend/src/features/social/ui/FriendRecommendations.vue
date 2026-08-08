<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { socialApi, type RecommendationItem } from '@/shared/api/social';

const props = withDefaults(defineProps<{
  limit?: number;
  compact?: boolean;
}>(), {
  limit: 12,
  compact: false,
});

const router = useRouter();
const items = ref<RecommendationItem[]>([]);
const loading = ref(false);

const categoryIcon = (cat: string) => {
  switch (cat) {
    case 'game': return '🎮';
    case 'movie': return '🎬';
    case 'series': return '📺';
    case 'anime': return '🎌';
    case 'manga': return '📖';
    case 'comics': return '💥';
    case 'book': return '📚';
    default: return '📝';
  }
};

onMounted(async () => {
  loading.value = true;
  try {
    items.value = await socialApi.getRecommendations(props.limit);
  } catch (e) {
    console.error('Failed to load recommendations', e);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <section v-if="loading || items.length > 0" class="recs">
    <div class="recs-header">
      <h2 class="recs-title">От друзей</h2>
      <p class="recs-sub">По пересечению жанров с вашей библиотекой</p>
    </div>

    <div v-if="loading" class="recs-loading">Загрузка рекомендаций…</div>

    <div v-else class="recs-grid" :class="{ compact }">
      <article
        v-for="item in items"
        :key="item.title.id"
        class="rec-card"
      >
        <div class="cover">
          <img
            v-if="item.title.cover_image"
            :src="item.title.cover_image"
            :alt="item.title.name"
          />
          <span v-else class="cover-fallback">{{ categoryIcon(item.title.category) }}</span>
        </div>
        <div class="rec-body">
          <div class="rec-name">
            <span class="cat">{{ categoryIcon(item.title.category) }}</span>
            {{ item.title.name }}
          </div>
          <div v-if="item.shared_genres.length" class="genres">
            <span v-for="g in item.shared_genres.slice(0, 3)" :key="g" class="genre">{{ g }}</span>
          </div>
          <div class="by">
            прошёл
            <button
              v-for="u in item.recommended_by"
              :key="u.id"
              type="button"
              class="friend-link"
              @click="router.push(`/user/${u.id}`)"
            >
              @{{ u.login }}
            </button>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.recs {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.recs-header {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.recs-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
}

.recs-sub {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.recs-loading {
  color: var(--color-text-muted);
}

.recs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 0.75rem;
}

.recs-grid.compact {
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}

.rec-card {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.9rem;
  background: var(--color-background-soft);
}

.cover {
  width: 3.5rem;
  height: 5rem;
  border-radius: 0.5rem;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-surface);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-fallback {
  font-size: 1.4rem;
}

.rec-body {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.rec-name {
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.3;
}

.cat {
  margin-right: 0.25rem;
}

.genres {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.genre {
  font-size: 0.75rem;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary-500) 12%, transparent);
  color: var(--color-text-secondary);
}

.by {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  align-items: center;
}

.friend-link {
  padding: 0;
  border: none;
  background: transparent;
  color: var(--color-primary-500);
  cursor: pointer;
  font: inherit;
}

.friend-link:hover {
  text-decoration: underline;
}
</style>
