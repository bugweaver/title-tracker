<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { listsApi, type UserListSummary } from '@/shared/api';

const router = useRouter();
const lists = ref<UserListSummary[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);
const newListName = ref('');
const isCreating = ref(false);

const loadLists = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    lists.value = await listsApi.list();
  } catch (e) {
    console.error(e);
    error.value = 'Не удалось загрузить списки';
  } finally {
    isLoading.value = false;
  }
};

const createList = async () => {
  const name = newListName.value.trim();
  if (!name || isCreating.value) return;
  isCreating.value = true;
  try {
    const created = await listsApi.create(name);
    newListName.value = '';
    router.push(`/lists/${created.id}`);
  } catch (e) {
    console.error(e);
    error.value = 'Не удалось создать список';
  } finally {
    isCreating.value = false;
  }
};

const openList = (id: number) => {
  router.push(`/lists/${id}`);
};

onMounted(loadLists);
</script>

<template>
  <div class="lists-page mx-auto flex max-w-3xl flex-col gap-6 px-4 py-8 sm:gap-8 sm:px-6 sm:py-10">
    <header class="flex flex-col gap-2">
      <h1 class="text-3xl font-extrabold text-text">Списки</h1>
      <p class="text-sm text-[var(--color-text-secondary)]">
        Избранное, перепройти, с друзьями — любые подборки из вашей библиотеки
      </p>
    </header>

    <form class="flex items-stretch gap-3" @submit.prevent="createList">
      <input
        v-model="newListName"
        type="text"
        maxlength="120"
        placeholder="Название нового списка"
        class="min-w-0 flex-1 rounded-xl border border-border bg-surface px-4 py-3 text-sm outline-none focus:border-primary-500"
      />
      <button
        type="submit"
        class="shrink-0 rounded-xl bg-primary-500 px-5 py-3 text-sm font-semibold text-white disabled:opacity-50"
        :disabled="!newListName.trim() || isCreating"
      >
        Создать
      </button>
    </form>

    <p v-if="error" class="text-sm text-red-500">{{ error }}</p>

    <div v-if="isLoading" class="text-sm text-[var(--color-text-secondary)]">
      Загрузка…
    </div>

    <div
      v-else-if="lists.length === 0"
      class="rounded-xl border border-dashed border-border px-6 py-12 text-center text-sm text-[var(--color-text-secondary)]"
    >
      Списков пока нет. Создайте первый выше.
    </div>

    <div v-else class="flex flex-col gap-4">
      <button
        v-for="list in lists"
        :key="list.id"
        type="button"
        class="flex w-full items-center justify-between gap-4 rounded-xl border border-border bg-surface px-5 py-5 text-left transition-colors hover:border-primary-500/40 hover:bg-background-soft"
        @click="openList(list.id)"
      >
        <div class="min-w-0">
          <h2 class="truncate text-lg font-bold text-text">{{ list.name }}</h2>
          <p class="mt-1.5 text-xs text-[var(--color-text-tertiary)]">
            Обновлён {{ new Date(list.updated_at).toLocaleDateString('ru-RU') }}
          </p>
        </div>
        <span class="shrink-0 rounded-full bg-background-soft px-3 py-1.5 text-sm font-medium text-[var(--color-text-secondary)]">
          {{ list.items_count }}
        </span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.lists-page {
  row-gap: 2rem;
}

.lists-page > * + * {
  margin-top: 0;
}

@media (min-width: 640px) {
  .lists-page {
    row-gap: 2.5rem;
  }
}
</style>
