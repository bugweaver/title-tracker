<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { AppInput, AppButton } from '@/shared/ui';
import { useFormValidation, rules } from '@/shared/composables';
import { useAuth } from '../composables';

const router = useRouter();
const success = ref(false);

const { form, errors, generalError, validate, setGeneralError, clearErrors } = useFormValidation(
  { email: '', login: '', password: '', name: '' },
  {
    email: {
      rules: [
        rules.required('Email обязателен'),
        rules.email('Некорректный email'),
      ],
    },
    login: {
      rules: [
        rules.required('Логин обязателен'),
        rules.minLength(3, 'Минимум 3 символа'),
        rules.alphanumeric('Только буквы, цифры и _'),
      ],
    },
    password: {
      rules: [rules.password('Минимум 8 символов, буквы и цифры')],
    },
  }
);

const { loading, register } = useAuth();

async function handleSubmit() {
  if (!validate()) return;
  clearErrors();

  await register(
    {
      email: form.email,
      login: form.login,
      password: form.password,
      name: form.name || undefined,
    },
    () => {
      success.value = true;
      setTimeout(() => router.push('/login'), 1500);
    },
    (error) => setGeneralError(error.detail || 'Ошибка регистрации')
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
    <h1 class="text-2xl font-bold text-text text-center">Регистрация</h1>
    <p class="text-sm text-text-muted text-center -mt-2">Создайте аккаунт для отслеживания тайтлов</p>

    <div 
      v-if="success" 
      class="p-4 bg-success-bg text-success rounded-xl text-center font-medium"
    >
      ✓ Регистрация успешна! Переход к входу...
    </div>

    <div 
      v-if="generalError" 
      class="p-4 bg-error-bg text-error rounded-xl text-center font-medium"
    >
      {{ generalError }}
    </div>

    <div class="flex flex-col gap-4">
      <AppInput
        id="email"
        v-model="form.email"
        type="email"
        label="Email"
        placeholder="your@email.com"
        :error="errors.email"
      />

      <AppInput
        id="login"
        v-model="form.login"
        type="text"
        label="Логин"
        placeholder="username"
        :error="errors.login"
      />

      <AppInput
        id="password"
        v-model="form.password"
        type="password"
        label="Пароль"
        placeholder="••••••••"
        :error="errors.password"
      />

      <AppInput
        id="name"
        v-model="form.name"
        type="text"
        label="Имя (необязательно)"
        placeholder="Как вас зовут?"
        :error="errors.name"
      />
    </div>

    <AppButton type="submit" :loading="loading" :disabled="success">
      Создать аккаунт
    </AppButton>

    <p class="text-sm text-text-muted text-center">
      Уже есть аккаунт?
      <RouterLink to="/login" class="text-primary-500 font-semibold hover:text-primary-600 transition-colors">
        Войти
      </RouterLink>
    </p>
  </form>
</template>
