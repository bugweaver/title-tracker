<script setup lang="ts">
import { onUnmounted, ref, watch } from 'vue';
import { listsApi, type UserListSummary } from '@/shared/api';

const props = defineProps<{
  userTitleId: number;
  open: boolean;
}>();

const emit = defineEmits<{
  close: [];
  added: [listId: number];
}>();

const menuRef = ref<HTMLElement | null>(null);
const lists = ref<UserListSummary[]>([]);
const isLoading = ref(false);
const isCreating = ref(false);
const newListName = ref('');
const error = ref<string | null>(null);
const busyListId = ref<number | null>(null);
let openTimer: number | null = null;

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

const addToList = async (listId: number) => {
  if (busyListId.value != null) return;
  busyListId.value = listId;
  error.value = null;
  try {
    await listsApi.addItem(listId, props.userTitleId);
    emit('added', listId);
    emit('close');
  } catch (e: unknown) {
    const detail = (e as { detail?: string })?.detail;
    error.value = detail === 'Already in this list'
      ? 'Уже в этом списке'
      : 'Не удалось добавить';
  } finally {
    busyListId.value = null;
  }
};

const createAndAdd = async () => {
  const name = newListName.value.trim();
  if (!name || isCreating.value) return;
  isCreating.value = true;
  error.value = null;
  try {
    const created = await listsApi.create(name);
    await listsApi.addItem(created.id, props.userTitleId);
    newListName.value = '';
    emit('added', created.id);
    emit('close');
  } catch (e) {
    console.error(e);
    error.value = 'Не удалось создать список';
  } finally {
    isCreating.value = false;
  }
};

const handleClickOutside = (event: MouseEvent) => {
  if (menuRef.value && !menuRef.value.contains(event.target as Node)) {
    emit('close');
  }
};

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') emit('close');
};

watch(
  () => props.open,
  (isOpen) => {
    if (openTimer !== null) {
      window.clearTimeout(openTimer);
      openTimer = null;
    }
    document.removeEventListener('click', handleClickOutside);
    document.removeEventListener('keydown', handleKeydown);

    if (isOpen) {
      loadLists();
      openTimer = window.setTimeout(() => {
        document.addEventListener('click', handleClickOutside);
        document.addEventListener('keydown', handleKeydown);
        openTimer = null;
      }, 0);
    }
  },
);

onUnmounted(() => {
  if (openTimer !== null) window.clearTimeout(openTimer);
  document.removeEventListener('click', handleClickOutside);
  document.removeEventListener('keydown', handleKeydown);
});
</script>

<template>
  <div
    v-if="open"
    ref="menuRef"
    class="absolute right-0 top-full z-40 mt-1.5 w-64 rounded-xl border border-border bg-surface p-2 shadow-xl"
    @click.stop
  >
    <p class="px-2 py-1 text-xs font-semibold uppercase tracking-wide text-[var(--color-text-tertiary)]">
      Добавить в список
    </p>

    <div v-if="isLoading" class="px-2 py-3 text-sm text-[var(--color-text-secondary)]">
      Загрузка…
    </div>

    <div v-else class="max-h-48 space-y-0.5 overflow-y-auto">
      <button
        v-for="list in lists"
        :key="list.id"
        type="button"
        class="flex min-h-10 w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition-colors hover:bg-background-soft disabled:opacity-50"
        :disabled="busyListId === list.id"
        @click="addToList(list.id)"
      >
        <span class="truncate">{{ list.name }}</span>
        <span class="ml-2 shrink-0 text-xs text-[var(--color-text-tertiary)]">
          {{ list.items_count }}
        </span>
      </button>
      <p v-if="lists.length === 0" class="px-2 py-2 text-sm text-[var(--color-text-secondary)]">
        Списков пока нет
      </p>
    </div>

    <div class="mt-2 border-t border-border pt-2">
      <div class="flex gap-1.5">
        <input
          v-model="newListName"
          type="text"
          maxlength="120"
          placeholder="Новый список"
          class="min-w-0 flex-1 rounded-lg border border-border bg-background px-2.5 py-2 text-sm outline-none focus:border-primary-500"
          @keydown.enter.prevent="createAndAdd"
        />
        <button
          type="button"
          class="rounded-lg bg-primary-500 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
          :disabled="!newListName.trim() || isCreating"
          @click="createAndAdd"
        >
          +
        </button>
      </div>
    </div>

    <p v-if="error" class="mt-2 px-2 text-xs text-red-500">{{ error }}</p>
  </div>
</template>
