<script setup lang="ts">
defineProps<{
  type?: 'button' | 'submit' | 'reset';
  variant?: 'primary' | 'secondary' | 'ghost';
  loading?: boolean;
  disabled?: boolean;
}>();
</script>

<template>
  <button
    :type="type ?? 'button'"
    class="relative inline-flex items-center justify-center gap-2 
           px-6 py-3.5 text-base font-semibold rounded-xl
           transition-all duration-300 outline-none cursor-pointer
           disabled:opacity-60 disabled:cursor-not-allowed"
    :class="[
      {
        'bg-gradient-to-br from-primary-500 to-primary-600 text-white shadow-lg shadow-primary-500/35 hover:not-disabled:-translate-y-0.5 hover:not-disabled:shadow-xl hover:not-disabled:shadow-primary-500/45 active:not-disabled:translate-y-0': variant === 'primary' || !variant,
        'bg-surface text-text border border-border hover:not-disabled:bg-surface-hover': variant === 'secondary',
        'bg-transparent text-primary-500 hover:not-disabled:bg-primary-500/10': variant === 'ghost',
      },
      { 'pointer-events-none': loading }
    ]"
    :disabled="disabled || loading"
  >
    <span 
      v-if="loading" 
      class="absolute w-5 h-5 border-2 border-transparent border-t-current rounded-full animate-spin"
    />
    <span :class="{ 'opacity-0': loading }">
      <slot />
    </span>
  </button>
</template>
