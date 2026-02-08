<script setup lang="ts">
defineProps<{
  type?: 'text' | 'email' | 'password';
  modelValue: string;
  placeholder?: string;
  label?: string;
  error?: string;
  id?: string;
}>();

defineEmits<{
  'update:modelValue': [value: string];
}>();
</script>

<template>
  <div class="flex flex-col gap-2 w-full">
    <label 
      v-if="label" 
      :for="id" 
      class="text-sm font-medium text-text"
    >
      {{ label }}
    </label>
    <input
      :id="id"
      :type="type ?? 'text'"
      :value="modelValue"
      :placeholder="placeholder"
      class="px-4 py-3.5 text-base rounded-xl
             bg-surface text-text
             border border-border
             placeholder:text-text-muted
             transition-all duration-300 outline-none
             focus:border-primary-500 focus:ring-3 focus:ring-primary-500/15"
      :class="{ 
        'border-error focus:border-error focus:ring-error/15': error 
      }"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <span v-if="error" class="text-xs text-error">
      {{ error }}
    </span>
  </div>
</template>
