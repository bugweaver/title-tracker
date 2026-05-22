<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { Check, ChevronDown } from 'lucide-vue-next';
import type { GamePlatform } from '@/entities/title';
import GamePlatformBadge from './GamePlatformBadge.vue';

const props = defineProps<{
  modelValue: GamePlatform | null;
  options: Array<{
    value: GamePlatform | null;
    label: string;
  }>;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: GamePlatform | null): void;
}>();

const isOpen = ref(false);
const containerRef = ref<HTMLElement | null>(null);

const selectedOption = computed(() =>
  props.options.find(option => option.value === props.modelValue)
);

const selectPlatform = (value: GamePlatform | null) => {
  emit('update:modelValue', value);
  isOpen.value = false;
};

const toggle = () => {
  isOpen.value = !isOpen.value;
};

const handleClickOutside = (event: MouseEvent) => {
  if (containerRef.value && !containerRef.value.contains(event.target as Node)) {
    isOpen.value = false;
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<template>
  <div class="space-y-2 pb-2">
    <label class="text-sm font-medium text-[var(--color-text-secondary)]">Платформа</label>
    <div ref="containerRef" class="relative w-full min-w-[200px]">
      <button
        type="button"
        class="w-full flex items-center justify-between px-3 py-2 text-sm rounded-lg
               bg-surface text-text border border-border
               hover:border-primary-500 transition-colors duration-200 outline-none
               focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
        :class="{ 'border-primary-500 ring-2 ring-primary-500/20': isOpen }"
        @click="toggle"
      >
        <span class="truncate block text-left">
          <GamePlatformBadge
            v-if="modelValue"
            :platform="modelValue"
            icon-size="md"
          />
          <span v-else class="text-text-muted">{{ selectedOption?.label || 'Не выбрана' }}</span>
        </span>
        <ChevronDown
          class="w-4 h-4 text-text-muted transition-transform duration-200 ml-2 shrink-0"
          :class="{ 'rotate-180': isOpen }"
        />
      </button>

      <Transition
        enter-active-class="transition duration-100 ease-out"
        enter-from-class="transform scale-95 opacity-0"
        enter-to-class="transform scale-100 opacity-100"
        leave-active-class="transition duration-75 ease-in"
        leave-from-class="transform scale-100 opacity-100"
        leave-to-class="transform scale-95 opacity-0"
      >
        <div
          v-if="isOpen"
          class="absolute z-50 w-full mt-1 bg-surface border border-border rounded-lg shadow-lg overflow-hidden flex flex-col"
        >
          <ul class="max-h-60 overflow-auto py-1 custom-scrollbar">
            <li
              v-for="option in options"
              :key="String(option.value)"
              class="px-3 py-2 text-sm text-text cursor-pointer hover:bg-primary-500/10 hover:text-primary-500 flex items-center justify-between transition-colors"
              :class="{ 'bg-primary-500/5 text-primary-500 font-medium': option.value === modelValue }"
              @click="selectPlatform(option.value)"
            >
              <GamePlatformBadge
                v-if="option.value"
                :platform="option.value"
                icon-size="md"
              />
              <span v-else>{{ option.label }}</span>
              <Check v-if="option.value === modelValue" class="w-4 h-4 text-primary-500" />
            </li>
          </ul>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: var(--color-border);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: var(--color-text-muted);
}
</style>
