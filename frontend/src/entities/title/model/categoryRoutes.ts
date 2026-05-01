import { TitleCategory, UserTitleStatus } from './types';

export const TITLE_CATEGORY_ROUTE_PATTERN = 'games|movies|shows|anime';
export const TITLE_STATUS_ROUTE_PATTERN = 'all|completed|playing|watching|dropped|planned|on-hold';

const categoryByRouteSegment: Record<string, TitleCategory> = {
  games: TitleCategory.GAME,
  movies: TitleCategory.MOVIE,
  shows: TitleCategory.SERIES,
  anime: TitleCategory.ANIME,
};

const routeSegmentByCategory: Record<TitleCategory, string> = {
  [TitleCategory.GAME]: 'games',
  [TitleCategory.MOVIE]: 'movies',
  [TitleCategory.SERIES]: 'shows',
  [TitleCategory.ANIME]: 'anime',
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
};

const routeSegmentByStatus: Record<UserTitleStatus, string> & { all: string } = {
  all: 'all',
  [UserTitleStatus.COMPLETED]: 'completed',
  [UserTitleStatus.PLAYING]: 'playing',
  [UserTitleStatus.WATCHING]: 'watching',
  [UserTitleStatus.DROPPED]: 'dropped',
  [UserTitleStatus.PLANNED]: 'planned',
  [UserTitleStatus.ON_HOLD]: 'on-hold',
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
    UserTitleStatus.ON_HOLD,
  ] as const;

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
