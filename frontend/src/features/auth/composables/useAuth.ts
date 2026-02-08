import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { authApi } from '../api';
import { useUserStore } from '@/entities/user';
import type { ApiError } from '@/shared/api';
import type { RegisterData, LoginData } from '../api';

export function useAuth() {
  const router = useRouter();
  const userStore = useUserStore();
  const loading = ref(false);

  async function login(
    data: LoginData,
    onError?: (error: ApiError) => void
  ): Promise<boolean> {
    loading.value = true;

    try {
      const tokens = await authApi.login(data);
      userStore.setTokens(tokens);
      await userStore.fetchCurrentUser();
      router.push('/');
      return true;
    } catch (err) {
      onError?.(err as ApiError);
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function register(
    data: RegisterData,
    onSuccess?: () => void,
    onError?: (error: ApiError) => void
  ): Promise<boolean> {
    loading.value = true;

    try {
      await authApi.register(data);
      onSuccess?.();
      return true;
    } catch (err) {
      onError?.(err as ApiError);
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function logout(): Promise<void> {
    await userStore.logout();
    router.push('/login');
  }

  return {
    loading,
    login,
    register,
    logout,
  };
}
