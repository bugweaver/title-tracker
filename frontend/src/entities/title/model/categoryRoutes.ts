import { TitleCategory, UserTitleStatus } from './types';

export const TITLE_CATEGORY_ROUTE_PATTERN = 'games|movies|shows|anime|manga|comics|books';
export const TITLE_STATUS_ROUTE_PATTERN = 'all|completed|playing|watching|dropped|planned|on-hold|wishlist';

const categoryByRouteSegment: Record<string, TitleCategory> = {
  games: TitleCategory.GAME,
  movies: TitleCategory.MOVIE,
  shows: TitleCategory.SERIES,
  anime: TitleCategory.ANIME,
  manga: TitleCategory.MANGA,
  comics: TitleCategory.COMICS,
  books: TitleCategory.BOOK,
};

const routeSegmentByCategory: Record<TitleCategory, string> = {
  [TitleCategory.GAME]: 'games',
  [TitleCategory.MOVIE]: 'movies',
  [TitleCategory.SERIES]: 'shows',
  [TitleCategory.ANIME]: 'anime',
  [TitleCategory.MANGA]: 'manga',
  [TitleCategory.COMICS]: 'comics',
  [TitleCategory.BOOK]: 'books',
};

export const getTitleCategoryFromRouteSegment = (categoryParam: unknown) => {
  const segment = Array.isArray(categoryParam) ? categoryParam[0] : categoryParam;
  return typeof segment === 'string'
    ? categoryByRouteSegment[segment] ?? TitleCategory.GAME
    : TitleCategory.GAME;
};

export const getTitleCategoryRouteSegment = (category: TitleCategory) =>
  routeSegmentByCategory[category];

const statusByRouteSegment: Record<string, UserTitleStatus | 'all'> = {
  all: 'all',
  completed: UserTitleStatus.COMPLETED,
  playing: UserTitleStatus.PLAYING,
  watching: UserTitleStatus.WATCHING,
  dropped: UserTitleStatus.DROPPED,
  planned: UserTitleStatus.PLANNED,
  'on-hold': UserTitleStatus.ON_HOLD,
  wishlist: UserTitleStatus.WISHLIST,
};

const routeSegmentByStatus: Record<UserTitleStatus, string> & { all: string } = {
  all: 'all',
  [UserTitleStatus.COMPLETED]: 'completed',
  [UserTitleStatus.PLAYING]: 'playing',
  [UserTitleStatus.WATCHING]: 'watching',
  [UserTitleStatus.DROPPED]: 'dropped',
  [UserTitleStatus.PLANNED]: 'planned',
  [UserTitleStatus.ON_HOLD]: 'on-hold',
  [UserTitleStatus.WISHLIST]: 'wishlist',
};

export const isReadingCategory = (category: TitleCategory | string) =>
  category === TitleCategory.MANGA
  || category === TitleCategory.COMICS
  || category === TitleCategory.BOOK
  || category === 'manga'
  || category === 'comics'
  || category === 'book';

export const getReplayCompletionLabel = (category: TitleCategory | string) => {
  if (category === TitleCategory.GAME || category === 'game') return 'Перепрохождение';
  if (isReadingCategory(category)) return 'Перечитка';
  return 'Пересмотр';
};

export const getTimesCompletedLabel = (
  timesCompleted: number,
  category: TitleCategory | string,
  options?: { compact?: boolean },
) => {
  if (timesCompleted <= 1) return null;

  if (options?.compact) return `×${timesCompleted}`;

  const isGame = category === TitleCategory.GAME || category === 'game';
  const isReading = isReadingCategory(category);
  const mod10 = timesCompleted % 10;
  const mod100 = timesCompleted % 100;
  const noun = mod10 === 1 && mod100 !== 11
    ? 'раз'
    : mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)
      ? 'раза'
      : 'раз';

  if (isGame) return `Пройдено ${timesCompleted} ${noun}`;
  if (isReading) return `Прочитано ${timesCompleted} ${noun}`;
  return `Просмотрено ${timesCompleted} ${noun}`;
};

export const getAvailableTitleStatuses = (category: TitleCategory) =>
  [
    'all',
    UserTitleStatus.COMPLETED,
    ...(category !== TitleCategory.MOVIE
      ? [category === TitleCategory.GAME ? UserTitleStatus.PLAYING : UserTitleStatus.WATCHING]
      : []),
    UserTitleStatus.DROPPED,
    UserTitleStatus.PLANNED,
    UserTitleStatus.WISHLIST,
    UserTitleStatus.ON_HOLD,
  ] as const;

export const supportsProgressTracking = (category: TitleCategory | string) =>
  category === TitleCategory.GAME
  || category === TitleCategory.MANGA
  || category === TitleCategory.COMICS
  || category === TitleCategory.BOOK
  || category === 'game'
  || category === 'manga'
  || category === 'comics'
  || category === 'book';

export const getProgressLabel = (category: TitleCategory | string) => {
  if (category === TitleCategory.GAME || category === 'game') return 'Часы';
  if (category === TitleCategory.MANGA || category === 'manga') return 'Главы';
  if (category === TitleCategory.BOOK || category === 'book') return 'Страницы';
  if (category === TitleCategory.COMICS || category === 'comics') return 'Тома';
  return 'Прогресс';
};

export const formatProgressValue = (
  value: number | null | undefined,
  category: TitleCategory | string,
) => {
  if (value == null || value < 0) return null;
  if (category === TitleCategory.GAME || category === 'game') return `${value} ч`;
  if (category === TitleCategory.MANGA || category === 'manga') return `${value} гл.`;
  if (category === TitleCategory.BOOK || category === 'book') return `${value} стр.`;
  if (category === TitleCategory.COMICS || category === 'comics') return `${value} т.`;
  return String(value);
};

export const getTitleStatusLabel = (
  status: UserTitleStatus | 'all' | string,
  category: TitleCategory | string,
  options?: { reviewForm?: boolean },
) => {
  if (status === 'all') return 'Все';

  const isGame = category === TitleCategory.GAME || category === 'game';
  const isReading = isReadingCategory(category);
  const reviewForm = options?.reviewForm ?? false;

  switch (status) {
    case UserTitleStatus.COMPLETED:
    case 'completed':
      if (isGame) return reviewForm ? 'Пройдено' : 'Прошел';
      if (isReading) return reviewForm ? 'Прочитано' : 'Прочитал';
      return reviewForm ? 'Просмотрено' : 'Посмотрел';
    case UserTitleStatus.PLAYING:
    case 'playing':
      return isGame ? 'Играю' : isReading ? 'Читаю' : 'Смотрю';
    case UserTitleStatus.WATCHING:
    case 'watching':
      return isReading ? 'Читаю' : 'Смотрю';
    case UserTitleStatus.DROPPED:
    case 'dropped':
      return reviewForm ? 'Дропнуто' : 'Дропнул';
    case UserTitleStatus.PLANNED:
    case 'planned':
      return 'В планах';
    case UserTitleStatus.WISHLIST:
    case 'wishlist':
      return 'Вишлист';
    case UserTitleStatus.ON_HOLD:
    case 'on_hold':
      return 'На паузе';
    default:
      return status;
  }
};

export const getTitleStatusFromRouteSegment = (
  statusParam: unknown,
  category: TitleCategory,
): UserTitleStatus | 'all' => {
  const segment = Array.isArray(statusParam) ? statusParam[0] : statusParam;
  const status = typeof segment === 'string'
    ? statusByRouteSegment[segment] ?? 'all'
    : 'all';
  const availableStatuses = getAvailableTitleStatuses(category);

  return availableStatuses.includes(status) ? status : 'all';
};

export const getTitleStatusRouteSegment = (status: UserTitleStatus | 'all') =>
  routeSegmentByStatus[status];
