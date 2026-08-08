<script setup lang="ts">
import BackupSettings from '@/features/backup/BackupSettings.vue';
import ProfileSettings from '@/features/user/ui/ProfileSettings.vue';
</script>

<template>
  <div class="mx-auto max-w-screen-xl px-4 py-5 sm:px-6 sm:py-8 lg:px-8">
    <h1 class="mb-5 text-2xl font-bold text-text sm:mb-8 sm:text-3xl">Настройки</h1>

    <div class="flex flex-col gap-6 sm:p-4">
      <ProfileSettings />
      <BackupSettings />
    </div>
  </div>
</template>
