<script setup lang="ts">
defineProps<{
  isOpen: boolean;
  urls: string[];
  currentIndex: number;
}>();

defineEmits<{
  (e: 'close'): void;
  (e: 'update:currentIndex', value: number): void;
}>();
</script>

<template>
  <Teleport to="body">
    <div
      v-if="isOpen && urls.length > 0"
      class="fixed inset-0 z-[200] bg-black/95 flex items-center justify-center"
      @click="$emit('close')"
    >
      <button
        class="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/10 hover:bg-white/25 border-none text-white text-xl cursor-pointer flex items-center justify-center transition-colors z-[201]"
        @click.stop="$emit('close')"
      >✕</button>
      <button
        v-if="currentIndex > 0"
        class="absolute left-5 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/10 hover:bg-white/25 border-none text-white text-4xl cursor-pointer flex items-center justify-center transition-colors z-[201]"
        @click.stop="$emit('update:currentIndex', currentIndex - 1)"
      >‹</button>
      <div class="flex flex-col items-center gap-3 max-w-[90vw] max-h-[90vh]" @click.stop>
        <img
          :src="urls[currentIndex]"
          class="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
        />
        <span class="text-white/60 text-sm">{{ currentIndex + 1 }} / {{ urls.length }}</span>
      </div>
      <button
        v-if="currentIndex < urls.length - 1"
        class="absolute right-5 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/10 hover:bg-white/25 border-none text-white text-4xl cursor-pointer flex items-center justify-center transition-colors z-[201]"
        @click.stop="$emit('update:currentIndex', currentIndex + 1)"
      >›</button>
    </div>
  </Teleport>
</template>
