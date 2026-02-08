<script setup lang="ts">
import { ref, watch } from 'vue';
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
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
    <div class="bg-surface border border-border rounded-xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b border-border">
        <h2 class="text-xl font-bold text-text">Редактирование фото</h2>
        <button @click="handleClose" class="text-text-secondary hover:text-text transition-colors">
          <X :size="24" />
        </button>
      </div>

      <!-- Cropper Area -->
      <div class="p-4 bg-background-soft flex-grow overflow-hidden flex items-center justify-center">
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
      <div class="p-4 border-t border-border flex justify-end gap-3 bg-surface">
        <button 
          @click="handleClose"
          class="px-4 py-2 text-text-secondary hover:text-text font-medium transition-colors"
        >
          Отмена
        </button>
        <button 
          @click="handleSave"
          class="px-6 py-2 bg-primary-500 hover:bg-primary-600 text-white font-bold rounded-lg transition-colors"
        >
          Сохранить
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cropper-wrapper {
  height: 400px;
  width: 100%;
  background-color: #000;
}
</style>
