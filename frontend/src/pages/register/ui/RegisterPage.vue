<script setup lang="ts">
import { RegisterForm } from '@/features/auth';
</script>

<template>
  <main class="auth-page">
    <RegisterForm />
  </main>
</template>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100dvh;
  padding: 1rem;
}

@media (min-width: 640px) {
  .auth-page {
    padding: 2rem;
  }
}
</style>
