<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/entities/user';
import { reviewsApi, type ReviewComment } from '@/shared/api/reviews';

const props = defineProps<{
  userTitleId: number;
  ownerId: number;
}>();

const router = useRouter();
const userStore = useUserStore();
const comments = ref<ReviewComment[]>([]);
const body = ref('');
const loading = ref(false);
const submitting = ref(false);

const canSubmit = computed(() => body.value.trim().length > 0 && !submitting.value);

const load = async () => {
  loading.value = true;
  try {
    comments.value = await reviewsApi.listComments(props.userTitleId);
  } catch (e) {
    console.error('Failed to load comments', e);
  } finally {
    loading.value = false;
  }
};

const submit = async () => {
  if (!canSubmit.value) return;
  submitting.value = true;
  try {
    const created = await reviewsApi.createComment(props.userTitleId, body.value.trim());
    comments.value.push(created);
    body.value = '';
  } catch (e) {
    console.error('Failed to create comment', e);
  } finally {
    submitting.value = false;
  }
};

const remove = async (comment: ReviewComment) => {
  try {
    await reviewsApi.deleteComment(props.userTitleId, comment.id);
    comments.value = comments.value.filter((c) => c.id !== comment.id);
  } catch (e) {
    console.error('Failed to delete comment', e);
  }
};

const canDelete = (comment: ReviewComment) =>
  comment.author.id === userStore.user?.id || props.ownerId === userStore.user?.id;

const formatTime = (dateStr: string) => {
  const date = new Date(dateStr);
  return date.toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
};

watch(() => props.userTitleId, load);
onMounted(load);
</script>

<template>
  <div class="comments">
    <h2 class="section-title">Комментарии</h2>

    <form class="comment-form" @submit.prevent="submit">
      <textarea
        v-model="body"
        rows="3"
        maxlength="2000"
        placeholder="Написать комментарий..."
        class="comment-input"
      />
      <button type="submit" class="submit-btn" :disabled="!canSubmit">
        {{ submitting ? 'Отправка…' : 'Отправить' }}
      </button>
    </form>

    <div v-if="loading" class="muted">Загрузка…</div>
    <div v-else-if="comments.length === 0" class="muted">Пока нет комментариев</div>

    <ul v-else class="comment-list">
      <li v-for="comment in comments" :key="comment.id" class="comment-item">
        <button
          type="button"
          class="author"
          @click="router.push(`/user/${comment.author.id}`)"
        >
          <span class="avatar">
            <img
              v-if="comment.author.avatar_url"
              :src="comment.author.avatar_url"
              alt=""
            />
            <span v-else>{{ comment.author.login.substring(0, 1).toUpperCase() }}</span>
          </span>
          <span class="author-meta">
            <span class="name">{{ comment.author.name || comment.author.login }}</span>
            <span class="time">{{ formatTime(comment.created_at) }}</span>
          </span>
        </button>
        <p class="body">{{ comment.body }}</p>
        <button
          v-if="canDelete(comment)"
          type="button"
          class="delete-btn"
          @click="remove(comment)"
        >
          Удалить
        </button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.comments {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--color-text);
}

.comment-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.comment-input {
  width: 100%;
  resize: vertical;
  min-height: 5rem;
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  background: var(--color-background);
  color: var(--color-text);
  font: inherit;
}

.comment-input:focus {
  outline: none;
  border-color: var(--color-primary-500);
}

.submit-btn {
  align-self: flex-end;
  min-height: 2.75rem;
  padding: 0.5rem 1.25rem;
  border: none;
  border-radius: 0.75rem;
  background: var(--color-primary-500);
  color: white;
  font-weight: 600;
  cursor: pointer;
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.muted {
  color: var(--color-text-muted);
  font-size: 0.95rem;
}

.comment-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.comment-item {
  position: relative;
  padding: 0.9rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 0.9rem;
  background: var(--color-background);
}

.author {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  color: inherit;
}

.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 999px;
  overflow: hidden;
  background: var(--color-primary-100);
  color: var(--color-primary-600);
  font-weight: 700;
  flex-shrink: 0;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.author-meta {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.name {
  font-weight: 600;
  color: var(--color-text);
}

.time {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.body {
  margin: 0.65rem 0 0;
  white-space: pre-wrap;
  color: var(--color-text);
  line-height: 1.45;
}

.delete-btn {
  margin-top: 0.5rem;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 0.85rem;
  cursor: pointer;
}

.delete-btn:hover {
  color: #ef4444;
}
</style>
