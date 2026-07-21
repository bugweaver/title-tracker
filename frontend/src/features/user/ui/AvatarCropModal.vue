<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue';
import { Cropper, CircleStencil } from 'vue-advanced-cropper';
import 'vue-advanced-cropper/dist/style.css';
import { X } from 'lucide-vue-next';

const props = defineProps<{
  isOpen: boolean;
  imageFile: File | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', blob: Blob): void;
}>();

const imageUrl = ref<string | null>(null);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const cropper = ref<any>(null);
let previousBodyOverflow = '';

watch(() => props.imageFile, (file) => {
  if (file) {
    if (imageUrl.value) {
      URL.revokeObjectURL(imageUrl.value);
    }
    imageUrl.value = URL.createObjectURL(file);
  } else {
    imageUrl.value = null;
  }
}, { immediate: true });

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    previousBodyOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = previousBodyOverflow;
  }
});

onUnmounted(() => {
  document.body.style.overflow = previousBodyOverflow;
  if (imageUrl.value) URL.revokeObjectURL(imageUrl.value);
});

const handleSave = () => {
    if (cropper.value) {
        const result = cropper.value.getResult();
        if (result.canvas) {
            result.canvas.toBlob((blob: Blob | null) => {
                if (blob) {
                    emit('save', blob);
                    emit('close');
                }
            }, 'image/jpeg');
        }
    }
};

const handleClose = () => {
    emit('close');
};
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm sm:p-4">
    <div class="flex h-[100dvh] w-full max-w-lg flex-col overflow-hidden bg-surface shadow-2xl sm:h-auto sm:max-h-[90dvh] sm:rounded-xl sm:border sm:border-border">
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-border px-4 pb-4 pt-[calc(1rem+env(safe-area-inset-top))] sm:p-4">
        <h2 class="text-lg font-bold text-text sm:text-xl">Редактирование фото</h2>
        <button @click="handleClose" class="flex h-11 w-11 items-center justify-center rounded-lg text-text-secondary transition-colors hover:bg-surface-hover hover:text-text" aria-label="Закрыть">
          <X :size="24" />
        </button>
      </div>

      <!-- Cropper Area -->
      <div class="flex min-h-0 flex-grow items-center justify-center overflow-hidden bg-background-soft p-3 sm:p-4">
        <Cropper
          ref="cropper"
          class="cropper-wrapper"
          :src="imageUrl"
          :stencil-component="CircleStencil"
          :stencil-props="{
            aspectRatio: 1/1,
          }"
        />
      </div>

      <!-- Footer -->
      <div class="grid grid-cols-2 gap-3 border-t border-border bg-surface p-4 pb-[calc(1rem+env(safe-area-inset-bottom))] sm:flex sm:justify-end">
        <button 
          @click="handleClose"
          class="min-h-11 px-4 py-2 font-medium text-text-secondary transition-colors hover:text-text"
        >
          Отмена
        </button>
        <button 
          @click="handleSave"
          class="min-h-11 rounded-lg bg-primary-500 px-6 py-2 font-bold text-white transition-colors hover:bg-primary-600"
        >
          Сохранить
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cropper-wrapper {
  height: min(400px, 55dvh);
  width: 100%;
  background-color: #000;
}
</style>
