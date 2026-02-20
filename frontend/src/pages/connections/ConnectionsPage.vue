<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { usersApi, type User } from '@/shared/api';

const route = useRoute();
const router = useRouter();
const userId = computed(() => Number(route.params.id));
const activeTab = computed(() => (route.query.tab === 'following' ? 'following' : 'followers'));

const users = ref<User[]>([]);
const profileUser = ref<User | null>(null);
const isLoading = ref(false);

const switchTab = (tab: string) => {
  router.replace({ query: { tab } });
};

const fetchData = async () => {
  isLoading.value = true;
  try {
    const profile = await usersApi.getUser(userId.value);
    profileUser.value = profile;

    if (activeTab.value === 'followers') {
      users.value = await usersApi.getFollowers(userId.value);
    } else {
      users.value = await usersApi.getFollowing(userId.value);
    }
  } catch (e) {
    console.error('Failed to load connections', e);
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchData);
watch([userId, activeTab], fetchData);
</script>

<template>
  <div class="connections-page">
    <!-- Back link -->
    <button class="back-link" @click="router.push(`/user/${userId}`)">
      ← Назад к профилю
    </button>

    <!-- Profile header -->
    <div class="profile-header" v-if="profileUser">
      <div class="profile-avatar">
        <img v-if="profileUser.avatar_url" :src="profileUser.avatar_url" alt="" class="avatar-img" />
        <span v-else class="avatar-letter">{{ profileUser.login.substring(0, 1).toUpperCase() }}</span>
      </div>
      <h1 class="profile-name">{{ profileUser.name || profileUser.login }}</h1>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button
        class="tab"
        :class="{ active: activeTab === 'followers' }"
        @click="switchTab('followers')"
      >
        Подписчики
      </button>
      <button
        class="tab"
        :class="{ active: activeTab === 'following' }"
        @click="switchTab('following')"
      >
        Подписки
      </button>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="loading">
      <div class="spinner"></div>
    </div>

    <!-- Empty -->
    <div v-else-if="users.length === 0" class="empty">
      {{ activeTab === 'followers' ? 'Нет подписчиков' : 'Нет подписок' }}
    </div>

    <!-- List -->
    <div v-else class="user-list">
      <div
        v-for="u in users"
        :key="u.id"
        class="user-card"
        @click="router.push(`/user/${u.id}`)"
      >
        <div class="user-avatar">
          <img v-if="u.avatar_url" :src="u.avatar_url" alt="" class="avatar-img" />
          <span v-else class="avatar-letter">{{ u.login.substring(0, 1).toUpperCase() }}</span>
        </div>
        <div class="user-info">
          <span class="user-name">{{ u.name || u.login }}</span>
          <span class="user-login">@{{ u.login }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.connections-page {
  max-width: 640px;
  margin: 0 auto;
  padding: 32px 16px;
}

.back-link {
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-size: 14px;
  cursor: pointer;
  padding: 4px 0;
  margin-bottom: 20px;
  transition: color 0.15s;
}

.back-link:hover {
  color: var(--color-primary-500);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.profile-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--color-primary-100);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-letter {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-primary-600);
}

.profile-name {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  background: var(--color-background-soft);
  border-radius: 10px;
  padding: 4px;
  border: 1px solid var(--color-border);
}

.tab {
  flex: 1;
  padding: 10px 16px;
  background: transparent;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.tab:hover {
  color: var(--color-text);
}

.tab.active {
  background: var(--color-primary-500);
  color: white;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.loading {
  display: flex;
  justify-content: center;
  padding: 48px;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty {
  text-align: center;
  padding: 48px 16px;
  color: var(--color-text-muted);
  font-size: 15px;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 12px;
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.user-card:hover {
  border-color: var(--color-primary-500);
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.1);
}

.user-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--color-primary-100);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 600;
  font-size: 15px;
  color: var(--color-text);
}

.user-login {
  font-size: 13px;
  color: var(--color-text-muted);
}
</style>
