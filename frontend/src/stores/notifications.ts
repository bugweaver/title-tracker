import { ref } from 'vue';
import { defineStore } from 'pinia';
import { notificationsApi, type NotificationData } from '@/shared/api/notifications';

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref<NotificationData[]>([]);
  const unreadCount = ref(0);
  const isLoading = ref(false);
  let pollTimer: ReturnType<typeof setInterval> | null = null;

  async function fetchNotifications() {
    isLoading.value = true;
    try {
      notifications.value = await notificationsApi.getNotifications();
    } catch (e) {
      console.error('Failed to fetch notifications', e);
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchUnreadCount() {
    try {
      const res = await notificationsApi.getUnreadCount();
      unreadCount.value = res.count;
    } catch {
      // silently fail for polling
    }
  }

  async function markAsRead(id: number) {
    try {
      const updated = await notificationsApi.markAsRead(id);
      // Update in local list
      const idx = notifications.value.findIndex(n => n.id === id);
      if (idx !== -1) {
        notifications.value[idx] = updated;
      }
      unreadCount.value = Math.max(0, unreadCount.value - 1);
    } catch (e) {
      console.error('Failed to mark as read', e);
    }
  }

  async function markAllAsRead() {
    try {
      await notificationsApi.markAllAsRead();
      notifications.value = notifications.value.map(n => ({ ...n, is_read: true }));
      unreadCount.value = 0;
    } catch (e) {
      console.error('Failed to mark all as read', e);
    }
  }

  async function clearRead() {
    try {
      await notificationsApi.clearRead();
      notifications.value = notifications.value.filter(n => !n.is_read);
    } catch (e) {
      console.error('Failed to clear notifications', e);
    }
  }

  function startPolling(intervalMs = 30000) {
    stopPolling();
    fetchUnreadCount();
    pollTimer = setInterval(fetchUnreadCount, intervalMs);
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  return {
    notifications,
    unreadCount,
    isLoading,
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    clearRead,
    startPolling,
    stopPolling,
  };
});
