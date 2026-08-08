import { computed, reactive, watch, type Ref } from 'vue';
import {
  GamePlatform,
  TitleCategory,
  type UserTitle,
} from '@/entities/title';

export interface LibraryFilterState {
  search: string;
  genre: string | null;
  releaseYear: number | null;
  platform: GamePlatform | null;
  minScore: number | null;
  hasReview: boolean;
  hasScreenshots: boolean;
}

export const createEmptyLibraryFilters = (): LibraryFilterState => ({
  search: '',
  genre: null,
  releaseYear: null,
  platform: null,
  minScore: null,
  hasReview: false,
  hasScreenshots: false,
});

export const applyLibraryFilters = (
  titles: UserTitle[],
  filters: LibraryFilterState,
) => {
  const query = filters.search.trim().toLowerCase();

  return titles.filter((title) => {
    if (query && !title.title.name.toLowerCase().includes(query)) {
      return false;
    }

    if (filters.genre && !(title.title.genres || []).includes(filters.genre)) {
      return false;
    }

    if (
      filters.releaseYear !== null
      && title.title.release_year !== filters.releaseYear
    ) {
      return false;
    }

    if (filters.platform !== null && title.game_platform !== filters.platform) {
      return false;
    }

    if (filters.minScore !== null) {
      if (title.score === null || title.score < filters.minScore) {
        return false;
      }
    }

    if (filters.hasReview && !title.review_text?.trim()) {
      return false;
    }

    if (filters.hasScreenshots && !(title.screenshots?.length)) {
      return false;
    }

    return true;
  });
};

export const useLibraryFilters = (
  sourceTitles: Ref<UserTitle[]>,
  category?: Ref<TitleCategory>,
) => {
  const filters = reactive(createEmptyLibraryFilters());

  const availableGenres = computed(() => {
    const genres = new Set<string>();
    sourceTitles.value.forEach((title) => {
      (title.title.genres || []).forEach((genre) => {
        if (genre) genres.add(genre);
      });
    });
    return Array.from(genres).sort((a, b) => a.localeCompare(b, 'ru'));
  });

  const availableReleaseYears = computed(() => {
    const years = new Set<number>();
    sourceTitles.value.forEach((title) => {
      if (title.title.release_year) {
        years.add(title.title.release_year);
      }
    });
    return Array.from(years).sort((a, b) => b - a);
  });

  const showPlatformFilter = computed(() =>
    !category || category.value === TitleCategory.GAME
  );

  const hasActiveFilters = computed(() =>
    Boolean(
      filters.search.trim()
      || filters.genre
      || filters.releaseYear !== null
      || filters.platform !== null
      || filters.minScore !== null
      || filters.hasReview
      || filters.hasScreenshots,
    )
  );

  const resetFilters = () => {
    Object.assign(filters, createEmptyLibraryFilters());
  };

  if (category) {
    watch(category, () => {
      filters.genre = null;
      filters.releaseYear = null;
      filters.platform = null;
      filters.minScore = null;
      filters.hasReview = false;
      filters.hasScreenshots = false;
    });
  }

  return {
    filters,
    availableGenres,
    availableReleaseYears,
    showPlatformFilter,
    hasActiveFilters,
    resetFilters,
    apply: (titles: UserTitle[]) => applyLibraryFilters(titles, filters),
  };
};

export const PLATFORM_FILTER_OPTIONS = [
  { value: null, label: 'Все платформы' },
  { value: GamePlatform.PC, label: 'PC' },
  { value: GamePlatform.PLAYSTATION, label: 'Playstation' },
  { value: GamePlatform.XBOX, label: 'Xbox' },
  { value: GamePlatform.NINTENDO, label: 'Nintendo' },
];

export const SCORE_FILTER_OPTIONS = [
  { value: null, label: 'Любая оценка' },
  { value: 9, label: '9+' },
  { value: 8, label: '8+' },
  { value: 7, label: '7+' },
  { value: 6, label: '6+' },
  { value: 5, label: '5+' },
];
