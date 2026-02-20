import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/entities/user'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
    // {
    //   path: '/register',
    //   name: 'register',
    //   component: () => import('@/pages/register').then(m => m.RegisterPage),
    //   meta: { guestOnly: true },
    // },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/pages/login').then(m => m.LoginPage),
      meta: { guestOnly: true },
    },
    {
      path: '/my-titles',
      name: 'my-titles',
      component: () => import('@/pages/my-titles').then(m => m.MyTitlesPage),
      meta: { requiresAuth: true },
    },
    {
      path: '/community',
      name: 'community',
      component: () => import('@/pages/community').then(m => m.CommunityPage),
      meta: { requiresAuth: true },
    },
    {
      path: '/user/:id',
      name: 'user-profile',
      component: () => import('@/pages/user-titles').then(m => m.UserTitlesPage),
      meta: { requiresAuth: true },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/pages/settings/SettingsPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/review/:id',
      name: 'review',
      component: () => import('@/pages/review/ReviewPage.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore();
  
  // Wait for auth init if needed (though it happens in App.vue, 
  // sometimes it's better to ensure it here if possible, 
  // but simpler check is usually enough if token exists)
  // Re-checking auth state might be needed if pages are refreshed.
  // userStore.initAuth() is called in App.vue, which mounts AFTER router is ready usually?
  // Actually App.vue mounts, then router view renders.
  // But navigation guards run before that?
  // Let's rely on token presence for initial redirect, assuming userStore helps.
  
  // Actually, we need to ensure pinia is active. usage inside guard is fine.
  
  // Check if we have a token but no user (page reload scenario)
  if (userStore.accessToken && !userStore.user) {
    try {
      await userStore.fetchCurrentUser();
    } catch (e) {
      console.error('Failed to restore session', e);
    }
  }

  const isAuthenticated = userStore.isAuthenticated;

  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'login' });
  } else if (to.meta.guestOnly && isAuthenticated) {
    next({ name: 'my-titles' });
  } else {
    next();
  }
});

export default router
