<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { reviewsApi, type ReactionType, type ReviewReactions } from '@/shared/api/reviews';

const props = defineProps<{
  userTitleId: number;
}>();

const REACTIONS: { type: ReactionType; emoji: string; label: string }[] = [
  { type: 'like', emoji: '👍', label: 'Нравится' },
  { type: 'love', emoji: '❤️', label: 'Любовь' },
  { type: 'laugh', emoji: '😂', label: 'Смех' },
  { type: 'wow', emoji: '😮', label: 'Вау' },
  { type: 'sad', emoji: '😢', label: 'Грустно' },
];

const data = ref<ReviewReactions>({ counts: {}, my_reaction: null, total: 0 });
const loading = ref(false);

const load = async () => {
  loading.value = true;
  try {
    data.value = await reviewsApi.getReactions(props.userTitleId);
  } catch (e) {
    console.error('Failed to load reactions', e);
  } finally {
    loading.value = false;
  }
};

const toggle = async (type: ReactionType) => {
  try {
    if (data.value.my_reaction === type) {
      await reviewsApi.deleteReaction(props.userTitleId);
      data.value = await reviewsApi.getReactions(props.userTitleId);
    } else {
      data.value = await reviewsApi.setReaction(props.userTitleId, type);
    }
  } catch (e) {
    console.error('Failed to set reaction', e);
  }
};

watch(() => props.userTitleId, load);
onMounted(load);
</script>

<template>
  <div class="reactions">
    <button
      v-for="r in REACTIONS"
      :key="r.type"
      type="button"
      class="reaction-btn"
      :class="{ active: data.my_reaction === r.type }"
      :title="r.label"
      :disabled="loading"
      @click="toggle(r.type)"
    >
      <span class="emoji">{{ r.emoji }}</span>
      <span v-if="data.counts[r.type]" class="count">{{ data.counts[r.type] }}</span>
    </button>
  </div>
</template>

<style scoped>
.reactions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.reaction-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-height: 2.5rem;
  padding: 0.35rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  background: var(--color-background-soft);
  color: var(--color-text);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.reaction-btn:hover {
  border-color: var(--color-primary-500);
  background: color-mix(in srgb, var(--color-primary-500) 8%, transparent);
}

.reaction-btn.active {
  border-color: var(--color-primary-500);
  background: color-mix(in srgb, var(--color-primary-500) 14%, transparent);
}

.emoji {
  font-size: 1.1rem;
  line-height: 1;
}

.count {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-secondary);
}
</style>
