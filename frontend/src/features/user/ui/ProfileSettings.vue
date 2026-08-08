<script setup lang="ts">
import { ref, watch } from 'vue';
import { usersApi } from '@/shared/api/users';
import { useUserStore } from '@/entities/user';
import type { ApiError } from '@/shared/api';

const userStore = useUserStore();

const name = ref(userStore.user?.name ?? '');
const bio = ref(userStore.user?.bio ?? '');
const isPrivate = ref(userStore.user?.is_private ?? false);
const isSaving = ref(false);
const error = ref<string | null>(null);
const success = ref<string | null>(null);

watch(
  () => userStore.user,
  (user) => {
    if (!user) return;
    name.value = user.name ?? '';
    bio.value = user.bio ?? '';
    isPrivate.value = user.is_private ?? false;
  },
  { immediate: true },
);

const handleSave = async () => {
  if (isSaving.value) return;
  isSaving.value = true;
  error.value = null;
  success.value = null;

  try {
    const updated = await usersApi.updateProfile({
      name: name.value.trim() || null,
      bio: bio.value.trim() || null,
      is_private: isPrivate.value,
    });
    userStore.setUser({
      ...userStore.user!,
      ...updated,
      email: userStore.user!.email,
    });
    success.value = 'Профиль сохранён';
  } catch (e) {
    const apiError = e as ApiError;
    error.value = apiError.detail || 'Не удалось сохранить профиль';
  } finally {
    isSaving.value = false;
  }
};
</script>

<template>
  <div class="rounded-xl border border-border bg-background-soft p-4 sm:p-6">
    <h2 class="mb-4 text-xl font-bold text-text">Профиль</h2>
    <p class="mb-5 text-sm text-text-secondary">
      Имя и описание видны на странице профиля. Закрытый профиль скрывает библиотеку от всех, кроме подписчиков.
    </p>

    <form class="flex flex-col gap-4" @submit.prevent="handleSave">
      <label class="flex flex-col gap-1.5">
        <span class="text-sm font-medium text-text">Имя</span>
        <input
          v-model="name"
          type="text"
          maxlength="50"
          class="min-h-11 rounded-lg border border-border bg-background px-3 text-text outline-none transition-colors focus:border-primary-500"
          placeholder="Как вас показывать"
        />
      </label>

      <label class="flex flex-col gap-1.5">
        <span class="text-sm font-medium text-text">О себе</span>
        <textarea
          v-model="bio"
          rows="4"
          maxlength="2000"
          class="rounded-lg border border-border bg-background px-3 py-2 text-text outline-none transition-colors focus:border-primary-500"
          placeholder="Коротко о вкусах, любимых жанрах…"
        />
      </label>

      <label class="flex min-h-11 cursor-pointer items-center gap-3">
        <input
          v-model="isPrivate"
          type="checkbox"
          class="h-4 w-4 rounded border-border text-primary-500 focus:ring-primary-500"
        />
        <span class="text-sm text-text">
          <span class="font-medium">Закрытый профиль</span>
          <span class="mt-0.5 block text-text-secondary">
            Библиотеку и отзывы видят только подписчики
          </span>
        </span>
      </label>

      <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
      <p v-if="success" class="text-sm text-green-600">{{ success }}</p>

      <button
        type="submit"
        class="min-h-11 w-full rounded-lg bg-primary-500 px-4 font-medium text-white transition-colors hover:bg-primary-600 disabled:opacity-60 sm:w-auto"
        :disabled="isSaving"
      >
        {{ isSaving ? 'Сохранение…' : 'Сохранить' }}
      </button>
    </form>
  </div>
</template>
