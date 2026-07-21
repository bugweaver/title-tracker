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
        class="lightbox-close absolute z-[201] flex h-11 w-11 cursor-pointer items-center justify-center rounded-full border-none bg-white/10 text-xl text-white transition-colors hover:bg-white/25"
        @click.stop="$emit('close')"
      >✕</button>
      <button
        v-if="currentIndex > 0"
        class="lightbox-nav lightbox-prev absolute z-[201] flex h-12 w-12 cursor-pointer items-center justify-center rounded-full border-none bg-white/10 text-4xl text-white transition-colors hover:bg-white/25"
        @click.stop="$emit('update:currentIndex', currentIndex - 1)"
      >‹</button>
      <div class="flex max-h-[calc(100dvh-7rem)] max-w-[calc(100vw-1.5rem)] flex-col items-center gap-3 sm:max-h-[90vh] sm:max-w-[90vw]" @click.stop>
        <img
          :src="urls[currentIndex]"
          class="max-h-[calc(100dvh-10rem)] max-w-full rounded-lg object-contain shadow-2xl sm:max-h-[85vh]"
        />
        <span class="text-white/60 text-sm">{{ currentIndex + 1 }} / {{ urls.length }}</span>
      </div>
      <button
        v-if="currentIndex < urls.length - 1"
        class="lightbox-nav lightbox-next absolute z-[201] flex h-12 w-12 cursor-pointer items-center justify-center rounded-full border-none bg-white/10 text-4xl text-white transition-colors hover:bg-white/25"
        @click.stop="$emit('update:currentIndex', currentIndex + 1)"
      >›</button>
    </div>
  </Teleport>
</template>

<style scoped>
.lightbox-close {
  top: max(1rem, env(safe-area-inset-top));
  right: 1rem;
}

.lightbox-nav {
  bottom: max(1rem, env(safe-area-inset-bottom));
}

.lightbox-prev {
  left: calc(50% - 58px);
}

.lightbox-next {
  right: calc(50% - 58px);
}

@media (min-width: 640px) {
  .lightbox-nav {
    top: 50%;
    bottom: auto;
    transform: translateY(-50%);
  }

  .lightbox-prev {
    left: 1.25rem;
  }

  .lightbox-next {
    right: 1.25rem;
  }
}
</style>
