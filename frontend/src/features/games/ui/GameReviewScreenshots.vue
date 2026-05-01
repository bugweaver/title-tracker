<script setup lang="ts">
import { ref } from 'vue';
import { type Screenshot } from '@/shared/api/titles';

defineProps<{
  existingScreenshots: Screenshot[];
  deletedScreenshotIds: number[];
  pendingPreviews: string[];
  totalScreenshots: number;
  maxScreenshots: number;
  canAddMore: boolean;
}>();

const emit = defineEmits<{
  (e: 'addFiles', files: File[]): void;
  (e: 'removePending', index: number): void;
  (e: 'deleteExisting', screenshot: Screenshot): void;
  (e: 'openPreview', url: string): void;
}>();

const fileInputRef = ref<HTMLInputElement | null>(null);
const isDragging = ref(false);

const openFileDialog = () => {
  fileInputRef.value?.click();
};

const onFileSelected = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files) {
    emit('addFiles', Array.from(input.files));
  }
  input.value = '';
};

const onDrop = (event: DragEvent) => {
  event.preventDefault();
  isDragging.value = false;

  if (event.dataTransfer?.files) {
    emit('addFiles', Array.from(event.dataTransfer.files));
  }
};

const onDragOver = (event: DragEvent) => {
  event.preventDefault();
  isDragging.value = true;
};

const onDragLeave = () => {
  isDragging.value = false;
};
</script>

<template>
  <div class="space-y-3">
    <label class="text-sm font-medium text-[var(--color-text-secondary)] block" style="margin-bottom: 12px;">
      Скриншоты
      <span class="text-[var(--color-text-muted)]">({{ totalScreenshots }}/{{ maxScreenshots }})</span>
    </label>

    <div v-if="existingScreenshots.length > 0" class="grid grid-cols-3 gap-2">
      <div
        v-for="screenshot in existingScreenshots"
        :key="screenshot.id"
        class="relative group rounded-lg overflow-hidden aspect-video bg-[var(--color-background-mute)]"
        :class="{ 'opacity-30': deletedScreenshotIds.includes(screenshot.id) }"
      >
        <img
          :src="screenshot.url"
          class="w-full h-full object-cover cursor-pointer"
          @click="!deletedScreenshotIds.includes(screenshot.id) && $emit('openPreview', screenshot.url)"
        />
        <div
          v-if="!deletedScreenshotIds.includes(screenshot.id)"
          class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            <line x1="11" y1="8" x2="11" y2="14"></line>
            <line x1="8" y1="11" x2="14" y2="11"></line>
          </svg>
        </div>
        <button
          v-if="!deletedScreenshotIds.includes(screenshot.id)"
          class="absolute top-1 right-1 w-6 h-6 bg-red-600 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-white text-xs z-10"
          title="Удалить"
          @click.stop="$emit('deleteExisting', screenshot)"
        >✕</button>
        <div
          v-else
          class="absolute inset-0 flex items-center justify-center bg-black/50 text-zinc-300 text-xs"
        >Удалён</div>
      </div>
    </div>

    <div v-if="pendingPreviews.length > 0" class="grid grid-cols-3 gap-2">
      <div
        v-for="(preview, index) in pendingPreviews"
        :key="'pending-' + index"
        class="relative group rounded-lg overflow-hidden aspect-video bg-[var(--color-background-mute)]"
      >
        <img
          :src="preview"
          class="w-full h-full object-cover cursor-pointer"
          @click="$emit('openPreview', preview)"
        />
        <div class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            <line x1="11" y1="8" x2="11" y2="14"></line>
            <line x1="8" y1="11" x2="14" y2="11"></line>
          </svg>
        </div>
        <button
          class="absolute top-1 right-1 w-6 h-6 bg-red-600 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-white text-xs z-10"
          title="Убрать"
          @click.stop="$emit('removePending', index)"
        >✕</button>
        <div class="absolute bottom-1 left-1 px-1.5 py-0.5 bg-[rgb(var(--review-tone-rgb)/0.85)] rounded text-[10px] text-white">Новый</div>
      </div>
    </div>

    <div
      v-if="canAddMore"
      class="border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors !mt-6"
      :class="isDragging
        ? 'border-[rgb(var(--review-tone-rgb))] bg-[rgb(var(--review-tone-rgb)/0.1)]'
        : 'border-[var(--color-border)] hover:border-[var(--color-border-hover)]'"
      @click="openFileDialog"
      @drop="onDrop"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
    >
      <input
        ref="fileInputRef"
        type="file"
        accept="image/*"
        multiple
        class="hidden"
        @change="onFileSelected"
      />
      <div class="flex flex-col items-center gap-1.5">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-[var(--color-text-muted)]">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <circle cx="8.5" cy="8.5" r="1.5"></circle>
          <polyline points="21 15 16 10 5 21"></polyline>
        </svg>
        <span class="text-xs text-[var(--color-text-muted)]">
          Перетащите или нажмите для загрузки
        </span>
        <span class="text-[10px] text-[var(--color-text-muted)]">JPEG, PNG, WebP, GIF • до 5 МБ</span>
      </div>
    </div>
  </div>
</template>
