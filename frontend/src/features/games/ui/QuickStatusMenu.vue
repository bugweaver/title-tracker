<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue';
import {
  TitleCategory,
  UserTitleStatus,
  getTitleStatusLabel,
  type UserTitle,
} from '@/entities/title';

const props = defineProps<{
  userTitle: UserTitle;
  open: boolean;
}>();

const emit = defineEmits<{
  close: [];
  select: [status: UserTitleStatus];
}>();

const menuRef = ref<HTMLElement | null>(null);
let openTimer: number | null = null;

const statuses = computed(() => {
  const category = props.userTitle.title.category;
  const isGame = category === TitleCategory.GAME;
  const isMovie = category === TitleCategory.MOVIE;

  return [
    UserTitleStatus.COMPLETED,
    ...(!isMovie
      ? [isGame ? UserTitleStatus.PLAYING : UserTitleStatus.WATCHING]
      : []),
    UserTitleStatus.DROPPED,
    UserTitleStatus.PLANNED,
    UserTitleStatus.WISHLIST,
    UserTitleStatus.ON_HOLD,
  ].map((status) => ({
    id: status,
    label: getTitleStatusLabel(status, category),
  }));
});

const handleClickOutside = (event: MouseEvent) => {
  if (menuRef.value && !menuRef.value.contains(event.target as Node)) {
    emit('close');
  }
};

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    emit('close');
  }
};

const detachListeners = () => {
  if (openTimer !== null) {
    window.clearTimeout(openTimer);
    openTimer = null;
  }
  document.removeEventListener('click', handleClickOutside);
  document.removeEventListener('keydown', handleKeydown);
};

watch(
  () => props.open,
  (isOpen) => {
    detachListeners();
    if (isOpen) {
      // Defer so the opening click does not immediately close the menu
      openTimer = window.setTimeout(() => {
        document.addEventListener('click', handleClickOutside);
        document.addEventListener('keydown', handleKeydown);
        openTimer = null;
      }, 0);
    }
  },
);

onUnmounted(() => {
  detachListeners();
});
</script>

<template>
  <div
    v-if="open"
    ref="menuRef"
    class="absolute left-0 top-full z-40 mt-1.5 min-w-[11rem] rounded-xl border border-border bg-surface p-1.5 shadow-xl"
    @click.stop
  >
    <button
      v-for="status in statuses"
      :key="status.id"
      type="button"
      class="flex min-h-10 w-full items-center rounded-lg px-3 py-2 text-left text-sm transition-colors"
      :class="status.id === userTitle.status
        ? 'bg-primary-100 font-medium text-primary-700'
        : 'text-text hover:bg-background-soft'"
      @click="emit('select', status.id)"
    >
      {{ status.label }}
    </button>
  </div>
</template>
