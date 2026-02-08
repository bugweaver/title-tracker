<script setup lang="ts" generic="T">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { ChevronDown, Check } from 'lucide-vue-next';

// Define props with generic type T for value
const props = defineProps<{
  modelValue: T | null;
  options: { value: T | null; label: string }[];
  placeholder?: string;
  label?: string;
  disabled?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: T | null): void;
}>();

const isOpen = ref(false);
const containerRef = ref<HTMLElement | null>(null);

const selectedLabel = computed(() => {
  const selected = props.options.find(opt => opt.value === props.modelValue);
  return selected ? selected.label : props.placeholder || 'Select...';
});

const toggle = () => {
  if (!props.disabled) {
    isOpen.value = !isOpen.value;
  }
};

const select = (optionValue: T | null) => {
  emit('update:modelValue', optionValue);
  isOpen.value = false;
};

// Start: Click outside logic
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
// End: Click outside logic

// Add smooth enter/leave transitions for dropdown
</script>

<template>
  <div ref="containerRef" class="relative w-full min-w-[200px]">
    <label 
      v-if="label" 
      class="block text-sm font-medium text-text mb-2"
    >
      {{ label }}
    </label>
    
    <button
      type="button"
      @click="toggle"
      class="w-full flex items-center justify-between px-3 py-2 text-sm rounded-lg
             bg-surface text-text border border-border
             hover:border-primary-500 transition-colors duration-200 outline-none
             focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
      :class="{ 
        'opacity-50 cursor-not-allowed': disabled,
        'border-primary-500 ring-2 ring-primary-500/20': isOpen
      }"
      :disabled="disabled"
    >
      <span class="truncate block text-left" :class="{ 'text-text-muted': !modelValue && placeholder }">
        {{ selectedLabel }}
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
            v-for="option in props.options"
            :key="String(option.value)"
            @click="select(option.value)"
            class="px-3 py-2 text-sm text-text cursor-pointer hover:bg-primary-500/10 hover:text-primary-500 flex items-center justify-between transition-colors"
            :class="{ 'bg-primary-500/5 text-primary-500 font-medium': option.value === modelValue }"
          >
            <span class="truncate">{{ option.label }}</span>
            <Check v-if="option.value === modelValue" class="w-4 h-4 text-primary-500" />
          </li>
        </ul>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* Custom scrollbar matching theme */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: var(--color-border); /* uses theme variable */
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: var(--color-text-muted);
}
</style>
