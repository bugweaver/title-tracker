<script setup lang="ts">
import { RouterLink } from 'vue-router';
import { useUserStore } from '@/entities/user';

const userStore = useUserStore();
</script>

<template>
  <div class="mx-auto min-h-[calc(100dvh-4rem)] max-w-screen-xl px-4 py-5 sm:px-6 sm:py-8 lg:px-8">
    <h1 class="mb-3 text-3xl font-bold tracking-tight text-text sm:text-4xl">Title Tracker</h1>
    <p class="max-w-2xl text-base leading-relaxed text-text-secondary sm:text-lg">
      Личный трекер игр, фильмов, сериалов, аниме, манги, комиксов и книг: статус, оценка, отзыв, скриншоты и прогресс по сезонам.
    </p>

    <section class="mt-8 max-w-2xl">
      <h2 class="mb-3 text-lg font-semibold text-text">Откуда берутся тайтлы</h2>
      <ul class="flex flex-col gap-2 text-sm text-text-secondary sm:text-base">
        <li><span class="font-medium text-text">IGDB</span> — игры и DLC</li>
        <li><span class="font-medium text-text">TMDB</span> — фильмы и сериалы</li>
        <li><span class="font-medium text-text">Shikimori</span> — аниме и манга</li>
        <li><span class="font-medium text-text">ComicVine</span> — комиксы</li>
        <li><span class="font-medium text-text">Google Books</span> — книги</li>
      </ul>
    </section>

    <section class="mt-8 max-w-2xl">
      <h2 class="mb-3 text-lg font-semibold text-text">Что можно делать</h2>
      <ul class="list-disc space-y-1 pl-5 text-sm text-text-secondary sm:text-base">
        <li>Вести библиотеку по категориям и статусам</li>
        <li>Писать отзывы со спойлерами и скриншотами</li>
        <li>Отмечать сезоны и серии, DLC у игр</li>
        <li>Подписываться на друзей и смотреть их библиотеки</li>
        <li>Экспортировать и импортировать резервную копию</li>
      </ul>
    </section>

    <div class="mt-10 flex flex-wrap gap-3">
      <RouterLink
        v-if="userStore.isAuthenticated"
        to="/settings"
        class="inline-flex min-h-11 items-center rounded-lg bg-primary-500 px-4 font-medium text-white transition-colors hover:bg-primary-600"
      >
        Настройки и бэкап
      </RouterLink>
      <RouterLink
        v-if="userStore.isAuthenticated"
        to="/my-titles"
        class="inline-flex min-h-11 items-center rounded-lg border border-border px-4 font-medium text-text transition-colors hover:bg-surface-hover"
      >
        Моя библиотека
      </RouterLink>
      <RouterLink
        v-else
        to="/login"
        class="inline-flex min-h-11 items-center rounded-lg bg-primary-500 px-4 font-medium text-white transition-colors hover:bg-primary-600"
      >
        Войти
      </RouterLink>
    </div>
  </div>
</template>
