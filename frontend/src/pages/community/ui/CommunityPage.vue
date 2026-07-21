<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { apiClient } from '@/shared/api';


interface User {
  id: number;
  login: string;
  name: string | null;
  avatar_url: string | null;
}

const users = ref<User[]>([]);
const isLoading = ref(false);
const searchQuery = ref('');

// Debounce helper
// eslint-disable-next-line @typescript-eslint/no-unsafe-function-type
const debounce = (fn: Function, ms = 300) => {
  let timeoutId: ReturnType<typeof setTimeout>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return function (this: any, ...args: any[]) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), ms);
  };
};

const fetchUsers = async () => {
  isLoading.value = true;
  try {
    // Construct query params
    const params = new URLSearchParams();
    params.append('limit', '50'); // Initial limit as requested "limited initially"
    if (searchQuery.value) {
      params.append('search', searchQuery.value);
    }
    
    // We need to support query params in apiClient or construct URL manually
    // Since apiClient.get usually takes endpoint, let's append params
    const queryString = params.toString() ? `?${params.toString()}` : '';
    // Fix: verify endpoint returns array or object with items
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const response = await apiClient.get<any>(`/users/${queryString}`);
    // If response is array, use it. If pagination object, use items.
    users.value = Array.isArray(response) ? response : (response.items || []);
  } catch (e) {
    console.error('Failed to fetch users', e);
  } finally {
    isLoading.value = false;
  }
};

const debouncedFetch = debounce(fetchUsers, 400);

watch(searchQuery, () => {
  debouncedFetch();
});

onMounted(() => {
  fetchUsers();
});


</script>

<template>
  <div class="mx-auto flex max-w-screen-xl flex-col gap-5 p-4 sm:gap-8 sm:p-6 lg:p-8">
    
    <div class="flex flex-col gap-4">
      <h1 class="text-2xl font-bold text-text sm:text-3xl">Сообщество</h1>
      <p class="text-text-muted">Ищите других пользователей и смотрите их коллекции</p>
    </div>

    <!-- Search -->
    <div class="w-full max-w-md">
      <input 
        v-model="searchQuery" 
        placeholder="Поиск пользователей..." 
        class="min-h-11 w-full rounded-lg border border-border bg-background-soft px-4 py-2 text-base text-text transition-colors focus:border-primary-500 focus:outline-none"
      />
    </div>

    <!-- Users Grid -->
    <div v-if="isLoading" class="flex justify-center p-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
    </div>
    
    <div v-else-if="users.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div 
        v-for="user in users" 
        :key="user.id"
        @click="$router.push(`/user/${user.id}`)"
        class="p-4 bg-background-soft border border-border rounded-xl flex items-center gap-4 hover:border-primary-500 transition-colors cursor-pointer group"
      >
        <div class="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center overflow-hidden flex-shrink-0">
          <img 
            v-if="user.avatar_url" 
            :src="user.avatar_url" 
            class="w-full h-full object-cover"
            alt="Avatar"
          />
          <span 
            v-else 
            class="text-lg font-bold text-primary-600 group-hover:text-primary-700 transition-colors"
          >
            {{ user.login.substring(0, 1).toUpperCase() }}
          </span>
        </div>
        
        <div class="overflow-hidden">
          <div class="font-bold text-text truncate">{{ user.name || user.login }}</div>
          <div class="text-sm text-text-muted truncate">@{{ user.login }}</div>
        </div>
      </div>
    </div>
        

    
    <div v-else class="rounded-xl border border-dashed border-border bg-background-soft py-12 text-center text-text-muted">
      Пользователи не найдены
    </div>

  </div>
</template>
