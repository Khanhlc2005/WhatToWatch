import { ParsedUrlQuery } from 'querystring';
import { genres } from '../config/genres';
import { MediaType } from '../types';

export type DiscoverFilters = {
  genreIds: number[];
  yearFrom: string;
  yearTo: string;
  minRating: string;
  maxRating: string;
  minRuntime: string;
  maxRuntime: string;
  language: string;
};

export const emptyFilters: DiscoverFilters = {
  genreIds: [], yearFrom: '', yearTo: '', minRating: '', maxRating: '', minRuntime: '', maxRuntime: '', language: ''
};

export const movieGenres = genres[MediaType.MOVIE];

export const languages: [string, string][] = [
  ['', 'Any language'], ['en', 'English'], ['fr', 'French'], ['ja', 'Japanese'], ['ko', 'Korean'],
  ['zh', 'Chinese'], ['es', 'Spanish'], ['vi', 'Vietnamese']
];

const numberKeys = ['yearFrom', 'yearTo', 'minRating', 'maxRating', 'minRuntime', 'maxRuntime'] as const;
const text = (value: string | string[] | undefined) => (typeof value === 'string' ? value : '');

// The URL holds the active filters so results can be shared.
export function filtersFromQuery(query: ParsedUrlQuery): DiscoverFilters {
  const filters: DiscoverFilters = { ...emptyFilters };
  filters.genreIds = text(query.genreIds).split(',').map(Number).filter(id => Number.isSafeInteger(id) && id > 0);
  numberKeys.forEach(key => { filters[key] = /^\d{1,4}(\.\d)?$/.test(text(query[key])) ? text(query[key]) : ''; });
  filters.language = /^[a-z]{2,3}$/.test(text(query.language)) ? text(query.language) : '';
  return filters;
}

export function queryFromFilters(filters: DiscoverFilters, page = 1): Record<string, string> {
  const query: Record<string, string> = {};
  if (filters.genreIds.length) query.genreIds = filters.genreIds.join(',');
  numberKeys.forEach(key => { if (filters[key] !== '') query[key] = filters[key]; });
  if (filters.language) query.language = filters.language;
  if (page > 1) query.page = String(page);
  return query;
}

export function pageFromQuery(query: ParsedUrlQuery): number {
  const page = Number(text(query.page) || 1);
  return Number.isSafeInteger(page) && page > 0 ? page : 1;
}

// Short labels for the active-filter chips above the results.
export function rangeLabel(from: string, to: string, prefix = '', suffix = ''): string | null {
  if (from === '' && to === '') return null;
  if (from !== '' && to !== '') return `${prefix}${from}–${to}${suffix}`;
  return from !== '' ? `${prefix}${from}+${suffix}` : `${prefix}up to ${to}${suffix}`;
}
