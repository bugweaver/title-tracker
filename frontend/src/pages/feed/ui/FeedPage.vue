<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { feedApi, type FeedItem } from '@/shared/api/feed';
import FriendRecommendations from '@/features/social/ui/FriendRecommendations.vue';
import { getTitleStatusLabel, type TitleCategory } from '@/entities/title';

const router = useRouter();
const items = ref<FeedItem[]>([]);
const loading = ref(true);
const loadingMore = ref(false);
const hasMore = ref(true);
const PAGE = 30;

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

const formatTime = (dateStr: string) => {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffH = Math.floor(diffMs / 3600000);
  const diffD = Math.floor(diffMs / 86400000);
  if (diffMin < 1) return 'только что';
  if (diffMin < 60) return `${diffMin} мин назад`;
  if (diffH < 24) return `${diffH} ч назад`;
  if (diffD < 7) return `${diffD} д назад`;
  return date.toLocaleDateString('ru-RU');
};

const load = async (reset = false) => {
  if (reset) {
    loading.value = true;
    items.value = [];
    hasMore.value = true;
  } else {
    loadingMore.value = true;
  }
  try {
    const offset = reset ? 0 : items.value.length;
    const page = await feedApi.getFeed(PAGE, offset);
    items.value = reset ? page : [...items.value, ...page];
    hasMore.value = page.length >= PAGE;
  } catch (e) {
    console.error('Failed to load feed', e);
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
};

onMounted(() => load(true));
</script>

<template>
  <div class="mx-auto flex max-w-screen-xl flex-col gap-6 p-4 sm:p-6 lg:p-8">
    <div>
      <h1 class="text-2xl font-bold text-text sm:text-3xl">Лента</h1>
      <p class="mt-1 text-text-muted">Активность людей, на которых вы подписаны</p>
    </div>

    <FriendRecommendations :limit="8" compact />

    <div v-if="loading" class="flex justify-center py-16">
      <div class="h-8 w-8 animate-spin rounded-full border-b-2 border-primary-500" />
    </div>

    <div
      v-else-if="items.length === 0"
      class="rounded-xl border border-dashed border-border bg-background-soft py-14 text-center text-text-muted"
    >
      Пока тихо. Подпишитесь на друзей в сообществе — их обновления появятся здесь.
    </div>

    <div v-else class="flex flex-col gap-3">
      <article
        v-for="item in items"
        :key="`${item.user_title_id}-${item.updated_at}`"
        class="flex cursor-pointer gap-3 rounded-xl border border-border bg-background-soft p-3 transition-colors hover:border-primary-500 sm:gap-4 sm:p-4"
        @click="router.push(`/review/${item.user_title_id}`)"
      >
        <button
          type="button"
          class="h-11 w-11 shrink-0 overflow-hidden rounded-full bg-primary-100"
          @click.stop="router.push(`/user/${item.actor.id}`)"
        >
          <img
            v-if="item.actor.avatar_url"
            :src="item.actor.avatar_url"
            alt=""
            class="h-full w-full object-cover"
          />
          <span
            v-else
            class="flex h-full w-full items-center justify-center font-bold text-primary-600"
          >
            {{ item.actor.login.substring(0, 1).toUpperCase() }}
          </span>
        </button>

        <div class="min-w-0 flex-1">
          <p class="text-sm text-text">
            <button
              type="button"
              class="font-semibold hover:underline"
              @click.stop="router.push(`/user/${item.actor.id}`)"
            >
              {{ item.actor.name || item.actor.login }}
            </button>
            {{ item.event === 'new' ? 'добавил' : 'обновил' }}
            <span class="font-medium">
              {{ categoryIcon(item.title.category) }} {{ item.title.name }}
            </span>
          </p>
          <div class="mt-1 flex flex-wrap items-center gap-2 text-sm text-text-muted">
            <span>{{ getTitleStatusLabel(item.status as any, item.title.category as TitleCategory) }}</span>
            <span v-if="item.score">· {{ item.score }}/10</span>
            <span>· {{ formatTime(item.updated_at) }}</span>
          </div>
          <p v-if="item.review_preview" class="mt-2 line-clamp-2 text-sm text-text-secondary">
            {{ item.review_preview }}
          </p>
        </div>

        <div
          v-if="item.title.cover_image"
          class="hidden h-20 w-14 shrink-0 overflow-hidden rounded-md sm:block"
        >
          <img :src="item.title.cover_image" :alt="item.title.name" class="h-full w-full object-cover" />
        </div>
      </article>

      <button
        v-if="hasMore"
        type="button"
        class="mx-auto mt-2 min-h-11 rounded-lg border border-border px-6 text-text transition-colors hover:bg-surface-hover"
        :disabled="loadingMore"
        @click="load(false)"
      >
        {{ loadingMore ? 'Загрузка…' : 'Ещё' }}
      </button>
    </div>
  </div>
</template>
