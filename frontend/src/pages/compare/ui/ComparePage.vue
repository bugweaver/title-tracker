<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  socialApi,
  type CompareBucket,
  type LibraryCompareResponse,
} from '@/shared/api/social';
import type { ApiError } from '@/shared/api';
import { getTitleStatusLabel, type TitleCategory } from '@/entities/title';

const route = useRoute();
const router = useRouter();
const userId = computed(() => Number(route.params.id));

const bucket = ref<CompareBucket>('both_completed');
const data = ref<LibraryCompareResponse | null>(null);
const loading = ref(true);
const error = ref('');

const tabs: { id: CompareBucket; label: string }[] = [
  { id: 'both_completed', label: 'Оба прошли' },
  { id: 'only_me', label: 'Только ты' },
  { id: 'only_them', label: 'Только друг' },
  { id: 'both_other', label: 'Оба в библиотеке' },
];

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

const load = async () => {
  loading.value = true;
  error.value = '';
  try {
    data.value = await socialApi.compareLibraries(userId.value, bucket.value);
  } catch (e) {
    const apiError = e as ApiError;
    error.value = apiError.detail || 'Не удалось сравнить библиотеки';
    data.value = null;
  } finally {
    loading.value = false;
  }
};

watch([userId, bucket], load);
onMounted(load);

const otherName = computed(
  () => data.value?.other_user.name || data.value?.other_user.login || 'друг',
);
</script>

<template>
  <div class="mx-auto flex max-w-screen-xl flex-col gap-5 p-4 sm:p-6 lg:p-8">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <button
          type="button"
          class="mb-2 text-sm text-primary-500 hover:underline"
          @click="router.push(`/user/${userId}`)"
        >
          ← К профилю
        </button>
        <h1 class="text-2xl font-bold text-text sm:text-3xl">Сравнение библиотек</h1>
        <p class="mt-1 text-text-muted">
          Вы и
          <button
            type="button"
            class="text-primary-500 hover:underline"
            @click="router.push(`/user/${userId}`)"
          >
            {{ otherName }}
          </button>
        </p>
      </div>
    </div>

    <div
      v-if="data"
      class="flex gap-2 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
    >
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        class="min-h-11 shrink-0 rounded-lg border px-3 py-2 text-sm transition-colors"
        :class="bucket === tab.id
          ? 'border-primary-500 bg-primary-500/10 text-primary-500'
          : 'border-border text-text hover:bg-surface-hover'"
        @click="bucket = tab.id"
      >
        {{ tab.label }}
        <span class="ml-1 text-text-muted">({{ data.counts[tab.id] }})</span>
      </button>
    </div>

    <div v-if="loading" class="flex justify-center py-16">
      <div class="h-8 w-8 animate-spin rounded-full border-b-2 border-primary-500" />
    </div>

    <div
      v-else-if="error"
      class="rounded-xl border border-border bg-background-soft px-4 py-10 text-center text-text-muted"
    >
      {{ error }}
    </div>

    <div
      v-else-if="!data?.items.length"
      class="rounded-xl border border-dashed border-border bg-background-soft py-14 text-center text-text-muted"
    >
      В этой категории пока пусто
    </div>

    <div v-else class="grid grid-cols-1 gap-3 md:grid-cols-2">
      <article
        v-for="item in data.items"
        :key="item.title.id"
        class="flex gap-3 rounded-xl border border-border bg-background-soft p-3"
      >
        <div class="h-24 w-16 shrink-0 overflow-hidden rounded-md bg-surface">
          <img
            v-if="item.title.cover_image"
            :src="item.title.cover_image"
            :alt="item.title.name"
            class="h-full w-full object-cover"
          />
          <div v-else class="flex h-full items-center justify-center text-xl">
            {{ categoryIcon(item.title.category) }}
          </div>
        </div>
        <div class="min-w-0 flex-1">
          <div class="font-semibold text-text">
            {{ categoryIcon(item.title.category) }} {{ item.title.name }}
          </div>
          <div class="mt-2 grid grid-cols-2 gap-2 text-sm">
            <div>
              <div class="text-text-muted">Ты</div>
              <div v-if="item.me.status" class="text-text">
                {{ getTitleStatusLabel(item.me.status as any, item.title.category as TitleCategory) }}
                <span v-if="item.me.score"> · {{ item.me.score }}</span>
              </div>
              <div v-else class="text-text-muted">—</div>
              <button
                v-if="item.me.user_title_id"
                type="button"
                class="mt-1 text-xs text-primary-500 hover:underline"
                @click="router.push(`/review/${item.me.user_title_id}`)"
              >
                Отзыв
              </button>
            </div>
            <div>
              <div class="text-text-muted">{{ otherName }}</div>
              <div v-if="item.them.status" class="text-text">
                {{ getTitleStatusLabel(item.them.status as any, item.title.category as TitleCategory) }}
                <span v-if="item.them.score"> · {{ item.them.score }}</span>
              </div>
              <div v-else class="text-text-muted">—</div>
              <button
                v-if="item.them.user_title_id"
                type="button"
                class="mt-1 text-xs text-primary-500 hover:underline"
                @click="router.push(`/review/${item.them.user_title_id}`)"
              >
                Отзыв
              </button>
            </div>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>
