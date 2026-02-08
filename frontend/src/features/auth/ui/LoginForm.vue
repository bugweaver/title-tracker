<script setup lang="ts">
import { AppInput, AppButton } from '@/shared/ui';
import { useFormValidation, rules } from '@/shared/composables';
import { useAuth } from '../composables';

const { form, errors, generalError, validate, setGeneralError, clearErrors } = useFormValidation(
  { username: '', password: '' },
  {
    username: { rules: [rules.required('Логин или email обязателен')] },
    password: { rules: [rules.required('Пароль обязателен')] },
  }
);

const { loading, login } = useAuth();

async function handleSubmit() {
  if (!validate()) return;
  clearErrors();

  await login(
    { username: form.username, password: form.password },
    (error) => setGeneralError(error.detail || 'Неверный логин или пароль')
  );
}
</script>

<template>
  <form 
    class="flex flex-col gap-6 w-full max-w-md p-10 
           bg-surface border border-border rounded-3xl 
           shadow-lg animate-fade-in" 
    @submit.prevent="handleSubmit"
  >
    <h1 class="text-2xl font-bold text-text text-center">Вход</h1>
    <p class="text-sm text-text-muted text-center -mt-2">Войдите в свой аккаунт</p>

    <div 
      v-if="generalError" 
      class="p-4 bg-error-bg text-error rounded-xl text-center font-medium"
    >
      {{ generalError }}
    </div>

    <div class="flex flex-col gap-4">
      <AppInput
        id="username"
        v-model="form.username"
        type="text"
        label="Логин или Email"
        placeholder="username или email"
        :error="errors.username"
      />

      <AppInput
        id="password"
        v-model="form.password"
        type="password"
        label="Пароль"
        placeholder="••••••••"
        :error="errors.password"
      />
    </div>

    <AppButton type="submit" :loading="loading">
      Войти
    </AppButton>

    <!-- <p class="text-sm text-text-muted text-center">
      Нет аккаунта?
      <RouterLink to="/register" class="text-primary-500 font-semibold hover:text-primary-600 transition-colors">
        Зарегистрироваться
      </RouterLink>
    </p> -->
  </form>
</template>
