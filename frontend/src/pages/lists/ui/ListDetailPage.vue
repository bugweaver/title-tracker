<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  formatProgressValue,
  getTitleStatusLabel,
} from '@/entities/title';
import { listsApi, type UserListDetail } from '@/shared/api';

const route = useRoute();
const router = useRouter();

const list = ref<UserListDetail | null>(null);
const isLoading = ref(true);
const error = ref<string | null>(null);
const isRenaming = ref(false);
const renameValue = ref('');
const isSavingName = ref(false);
const removingId = ref<number | null>(null);

const listId = computed(() => Number(route.params.id));

const loadList = async () => {
  if (!listId.value) return;
  isLoading.value = true;
  error.value = null;
  try {
    list.value = await listsApi.get(listId.value);
    renameValue.value = list.value.name;
  } catch (e) {
    console.error(e);
    error.value = 'Список не найден';
    list.value = null;
  } finally {
    isLoading.value = false;
  }
};

const saveRename = async () => {
  if (!list.value || isSavingName.value) return;
  const name = renameValue.value.trim();
  if (!name) return;
  isSavingName.value = true;
  try {
    const updated = await listsApi.rename(list.value.id, name);
    list.value = { ...list.value, name: updated.name, updated_at: updated.updated_at };
    isRenaming.value = false;
  } catch (e) {
    console.error(e);
    error.value = 'Не удалось переименовать';
  } finally {
    isSavingName.value = false;
  }
};

const removeItem = async (userTitleId: number) => {
  if (!list.value || removingId.value != null) return;
  removingId.value = userTitleId;
  try {
    await listsApi.removeItem(list.value.id, userTitleId);
    list.value = {
      ...list.value,
      items: list.value.items.filter((item) => item.user_title_id !== userTitleId),
    };
  } catch (e) {
    console.error(e);
    error.value = 'Не удалось удалить из списка';
  } finally {
    removingId.value = null;
  }
};

const deleteList = async () => {
  if (!list.value) return;
  if (!window.confirm(`Удалить список «${list.value.name}»?`)) return;
  try {
    await listsApi.remove(list.value.id);
    router.push('/lists');
  } catch (e) {
    console.error(e);
    error.value = 'Не удалось удалить список';
  }
};

const openReview = (userTitleId: number) => {
  router.push(`/review/${userTitleId}`);
};

watch(listId, loadList);
onMounted(loadList);
</script>

<template>
  <div class="mx-auto max-w-3xl px-4 py-8">
    <button
      type="button"
      class="mb-6 text-sm font-medium text-primary-500 hover:underline"
      @click="router.push('/lists')"
    >
      ← Все списки
    </button>

    <div v-if="isLoading" class="text-sm text-[var(--color-text-secondary)]">
      Загрузка…
    </div>

    <div v-else-if="!list" class="text-sm text-red-500">
      {{ error || 'Список не найден' }}
    </div>

    <template v-else>
      <div class="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div class="min-w-0 flex-1">
          <div v-if="isRenaming" class="flex flex-wrap gap-2">
            <input
              v-model="renameValue"
              type="text"
              maxlength="120"
              class="min-w-0 flex-1 rounded-lg border border-border bg-surface px-3 py-2 text-lg font-bold outline-none focus:border-primary-500"
              @keydown.enter.prevent="saveRename"
            />
            <button
              type="button"
              class="rounded-lg bg-primary-500 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
              :disabled="isSavingName || !renameValue.trim()"
              @click="saveRename"
            >
              Сохранить
            </button>
            <button
              type="button"
              class="rounded-lg border border-border px-3 py-2 text-sm"
              @click="isRenaming = false; renameValue = list.name"
            >
              Отмена
            </button>
          </div>
          <template v-else>
            <h1 class="truncate text-3xl font-extrabold text-text">{{ list.name }}</h1>
            <p class="mt-1 text-sm text-[var(--color-text-secondary)]">
              {{ list.items.length }} в списке
            </p>
          </template>
        </div>

        <div class="flex gap-2">
          <button
            type="button"
            class="rounded-lg border border-border px-3 py-2 text-sm hover:bg-background-soft"
            @click="isRenaming = true"
          >
            Переименовать
          </button>
          <button
            type="button"
            class="rounded-lg border border-red-300 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
            @click="deleteList"
          >
            Удалить
          </button>
        </div>
      </div>

      <p v-if="error" class="mb-4 text-sm text-red-500">{{ error }}</p>

      <div
        v-if="list.items.length === 0"
        class="rounded-xl border border-dashed border-border px-6 py-12 text-center text-sm text-[var(--color-text-secondary)]"
      >
        Список пуст. Добавляйте тайтлы из библиотеки кнопкой «в список».
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="item in list.items"
          :key="item.id"
          class="flex cursor-pointer gap-4 rounded-xl border border-border bg-surface p-3 transition-colors hover:border-primary-500/40 sm:p-4"
          @click="openReview(item.user_title_id)"
        >
          <div class="h-24 w-16 shrink-0 overflow-hidden rounded-lg bg-background-soft">
            <img
              v-if="item.title.cover_image"
              :src="item.title.cover_image"
              :alt="item.title.name"
              class="h-full w-full object-cover"
            />
          </div>
          <div class="min-w-0 flex-1">
            <h2 class="truncate text-lg font-bold text-text">{{ item.title.name }}</h2>
            <p class="mt-1 text-sm text-[var(--color-text-secondary)]">
              {{ getTitleStatusLabel(item.status, item.title.category) }}
              <template v-if="item.score != null"> · ★ {{ item.score }}</template>
              <template v-if="formatProgressValue(item.progress_value, item.title.category)">
                · {{ formatProgressValue(item.progress_value, item.title.category) }}
              </template>
            </p>
          </div>
          <button
            type="button"
            class="self-start rounded-lg px-2 py-1 text-sm text-[var(--color-text-tertiary)] hover:bg-background-soft hover:text-red-500 disabled:opacity-50"
            :disabled="removingId === item.user_title_id"
            title="Убрать из списка"
            @click.stop="removeItem(item.user_title_id)"
          >
            ✕
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
