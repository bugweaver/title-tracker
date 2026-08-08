import { apiClient } from './client';

export interface NamedCount {
  name: string;
  count: number;
}

export interface MonthCount {
  month: number;
  count: number;
}

export interface DayCount {
  day: number;
  count: number;
}

export interface YearStats {
  year: number;
  month: number | null;
  completed_count: number;
  average_score: number | null;
  top_genres: NamedCount[];
  monthly_heatmap: MonthCount[];
  daily_heatmap: DayCount[];
  by_platform: NamedCount[];
  by_category: NamedCount[];
}

export const statsApi = {
  getYearStats: (year: number, month?: number | null) => {
    const params = new URLSearchParams({ year: String(year) });
    if (month != null) {
      params.set('month', String(month));
    }
    return apiClient.get<YearStats>(`/stats/year?${params.toString()}`);
  },
};
