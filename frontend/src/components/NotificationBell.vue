<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useNotificationStore } from '@/stores/notifications';
import type { NotificationData } from '@/shared/api/notifications';

const router = useRouter();
const store = useNotificationStore();
const isOpen = ref(false);

onMounted(() => {
  store.startPolling();
});

onUnmounted(() => {
  store.stopPolling();
});

function toggleDropdown() {
  isOpen.value = !isOpen.value;
  if (isOpen.value && store.notifications.length === 0) {
    store.fetchNotifications();
  }
}

function closeDropdown() {
  isOpen.value = false;
}

async function handleNotificationClick(notification: NotificationData) {
  if (!notification.is_read) {
    await store.markAsRead(notification.id);
  }
  isOpen.value = false;
  if (notification.type === 'new_follower') {
    router.push(`/user/${notification.actor.id}`);
  } else {
    router.push(`/review/${notification.user_title_id}`);
  }
}

async function handleMarkAllRead() {
  await store.markAllAsRead();
}

function formatTime(dateStr: string) {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffH = Math.floor(diffMs / 3600000);
  const diffD = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return 'только что';
  if (diffMin < 60) return `${diffMin} мин назад`;
  if (diffH < 24) return `${diffH} ч назад`;
  if (diffD < 7) return `${diffD} д назад`;
  return date.toLocaleDateString('ru-RU');
}

const categoryIcon = (cat: string) => {
  switch (cat) {
    case 'game': return '🎮';
    case 'movie': return '🎬';
    case 'series': return '📺';
    case 'anime': return '🎌';
    default: return '📝';
  }
};
</script>

<template>
  <div class="notification-bell-wrapper">
    <!-- Bell button -->
    <button
      class="notification-bell"
      @click="toggleDropdown"
      title="Уведомления"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
      </svg>
      <span v-if="store.unreadCount > 0" class="notification-badge">
        {{ store.unreadCount > 99 ? '99+' : store.unreadCount }}
      </span>
    </button>

    <!-- Dropdown -->
    <Teleport to="body">
      <div v-if="isOpen" class="notification-overlay" @click="closeDropdown"></div>
    </Teleport>

    <Transition name="dropdown">
      <div v-if="isOpen" class="notification-dropdown">
        <div class="notification-header">
          <h3>Уведомления</h3>
          <button
            v-if="store.unreadCount > 0"
            class="mark-all-btn"
            @click="handleMarkAllRead"
          >
            Прочитать все
          </button>
        </div>

        <div v-if="store.isLoading" class="notification-loading">
          <div class="spinner"></div>
        </div>

        <div v-else-if="store.notifications.length === 0" class="notification-empty">
          Нет уведомлений
        </div>

        <div v-else class="notification-list">
          <div
            v-for="n in store.notifications"
            :key="n.id"
            class="notification-item"
            :class="{ unread: !n.is_read }"
            @click="handleNotificationClick(n)"
          >
            <div class="notification-avatar">
              <img
                v-if="n.actor.avatar_url"
                :src="n.actor.avatar_url"
                alt=""
                class="avatar-img"
              />
              <span v-else class="avatar-placeholder">
                {{ n.actor.login.substring(0, 1).toUpperCase() }}
              </span>
            </div>
            <div class="notification-content">
              <p class="notification-text">
                <strong>{{ n.actor.name || n.actor.login }}</strong>
                <template v-if="n.type === 'new_follower'">
                  подписался на вас
                </template>
                <template v-else>
                  {{ n.type === 'title_updated' ? 'обновил тайтл' : 'добавил тайтл' }}
                  <span class="title-name">{{ categoryIcon(n.title?.category ?? '') }} {{ n.title?.name }}</span>
                </template>
              </p>
              <span class="notification-time">{{ formatTime(n.created_at) }}</span>
            </div>
            <div v-if="!n.is_read" class="unread-dot"></div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.notification-bell-wrapper {
  position: relative;
}

.notification-bell {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 6px;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  color: var(--color-text);
  transition: all 0.2s;
  position: relative;
}

.notification-bell:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-border-hover);
}

.notification-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
  font-size: 11px;
  font-weight: 700;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.4);
  animation: badge-pop 0.3s ease-out;
}

@keyframes badge-pop {
  0% { transform: scale(0); }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); }
}

.notification-overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
}

.notification-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 380px;
  max-height: 480px;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25);
  z-index: 50;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.notification-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-border);
}

.notification-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
}

.mark-all-btn {
  background: none;
  border: none;
  color: var(--color-primary-500);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.15s;
}

.mark-all-btn:hover {
  background: var(--color-primary-500-10, rgba(99, 102, 241, 0.1));
}

.notification-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.notification-empty {
  padding: 32px 16px;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 14px;
}

.notification-list {
  overflow-y: auto;
  max-height: 400px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.15s;
  position: relative;
  border-bottom: 1px solid var(--color-border);
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item:hover {
  background: var(--color-surface-hover, rgba(255,255,255,0.04));
}

.notification-item.unread {
  background: var(--color-primary-500-5, rgba(99, 102, 241, 0.05));
}

.notification-item.unread:hover {
  background: var(--color-primary-500-10, rgba(99, 102, 241, 0.1));
}

.notification-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-primary-100);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-primary-600);
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-text {
  margin: 0 0 4px;
  font-size: 13px;
  line-height: 1.4;
  color: var(--color-text);
}

.notification-text strong {
  font-weight: 600;
}

.title-name {
  color: var(--color-primary-500);
  font-weight: 500;
}

.notification-time {
  font-size: 12px;
  color: var(--color-text-muted);
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary-500);
  flex-shrink: 0;
  margin-top: 6px;
}

/* Transition */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
