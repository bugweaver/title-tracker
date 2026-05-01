<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{
  modelValue: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

const textareaRef = ref<HTMLTextAreaElement | null>(null);

const insertSpoiler = () => {
  if (!textareaRef.value) return;

  const el = textareaRef.value;
  const start = el.selectionStart;
  const end = el.selectionEnd;
  const before = props.modelValue.substring(0, start);
  const selection = props.modelValue.substring(start, end);
  const after = props.modelValue.substring(end);

  emit('update:modelValue', before + '<' + (selection || 'спойлер') + '>' + after);

  setTimeout(() => {
    el.focus();
    const newCursorPos = start + 1 + (selection.length || 7) + 1;
    el.setSelectionRange(newCursorPos, newCursorPos);
  }, 0);
};
</script>

<template>
  <div class="space-y-2">
    <textarea
      ref="textareaRef"
      :value="modelValue"
      class="w-full h-32 bg-[var(--color-background-mute)] rounded-lg p-3 text-[var(--color-text)] resize-none outline-none focus:ring-2 focus:ring-[rgb(var(--review-tone-rgb))] placeholder:text-[var(--color-text-muted)] transition-colors"
      placeholder="Напишите ваше мнение..."
      maxlength="5000"
      @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    ></textarea>
    <div class="flex justify-between pl-2 items-center">
      <span class="text-xs text-[var(--color-text-muted)]">{{ modelValue.length }} / 5000</span>

      <button
        type="button"
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-hover)]"
        title="Обернуть выделенный текст в спойлер"
        @click="insertSpoiler"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
          <line x1="1" y1="1" x2="23" y2="23"></line>
        </svg>
        Спойлер
      </button>
    </div>
  </div>
</template>
