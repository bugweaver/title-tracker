<script setup lang="ts">
import AppButton from '@/shared/ui/AppButton.vue';

defineProps<{
  hasUserTitle: boolean;
  showDeleteConfirm: boolean;
  isDeleting: boolean;
  isSubmitting: boolean;
  isUploadingScreenshots: boolean;
}>();

defineEmits<{
  (e: 'update:showDeleteConfirm', value: boolean): void;
  (e: 'close'): void;
  (e: 'submit'): void;
  (e: 'delete'): void;
}>();
</script>

<template>
  <div v-if="showDeleteConfirm" class="p-4 border-t border-red-500/30 bg-red-500/5">
    <div class="flex items-center gap-3 mb-3">
      <div class="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
          <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
        </svg>
      </div>
      <p class="text-sm text-[var(--color-text-secondary)]">Тайтл, оценка, отзыв и скриншоты будут удалены безвозвратно.</p>
    </div>
    <div class="grid grid-cols-2 gap-2 sm:flex sm:justify-end">
      <button
        :disabled="isDeleting"
        class="min-h-11 cursor-pointer rounded-lg px-4 py-2 text-sm font-medium text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)]"
        @click="$emit('update:showDeleteConfirm', false)"
      >Отмена</button>
      <button
        :disabled="isDeleting"
        class="flex min-h-11 cursor-pointer items-center justify-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-500 disabled:opacity-50"
        @click="$emit('delete')"
      >
        <svg v-if="isDeleting" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
        {{ isDeleting ? 'Удаление...' : 'Да, удалить' }}
      </button>
    </div>
  </div>

  <div v-else class="game-review-footer flex flex-col-reverse gap-3 p-4 pb-[calc(1rem+env(safe-area-inset-bottom))] sm:flex-row sm:justify-between">
    <div class="flex">
      <button
        v-if="hasUserTitle"
        class="min-h-11 w-full cursor-pointer rounded-lg px-4 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/10 hover:text-red-300 sm:w-auto"
        @click="$emit('update:showDeleteConfirm', true)"
      >Удалить</button>
    </div>
    <div class="grid grid-cols-2 gap-3 sm:flex">
      <AppButton variant="ghost" @click="$emit('close')">Отмена</AppButton>
      <AppButton :loading="isSubmitting || isUploadingScreenshots" @click="$emit('submit')">
        {{ isUploadingScreenshots ? 'Загрузка...' : (hasUserTitle ? 'Обновить' : 'Добавить') }}
      </AppButton>
    </div>
  </div>
</template>

<style scoped>
.game-review-footer {
  background-color: color-mix(in srgb, rgb(var(--review-tone-rgb)) var(--review-footer-tint, 6%), var(--color-surface));
  border-top: 1px solid color-mix(in srgb, rgb(var(--review-tone-rgb)) 18%, var(--color-border));
  transition: background-color 450ms ease, border-color 450ms ease;
}
</style>
