import { NextApiRequest, NextApiResponse } from 'next';
import { allowMethod, sendError } from '../../../lib/api';
import { backendRequest } from '../../../lib/backend';
import { MovieSummary, PageResult } from '../../../lib/movies';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'GET')) return;
  const params = new URLSearchParams();
  const limit = Math.min(Math.max(Number(req.query.limit || 20), 1), 50);
  params.set('page', '0');
  params.set('size', String(limit));

  const rawGenreIds = req.query.genreIds;
  const genreList = Array.isArray(rawGenreIds)
    ? rawGenreIds.join(',').split(',')
    : typeof rawGenreIds === 'string'
      ? rawGenreIds.split(',')
      : [];

  for (const id of genreList) {
    const trimmed = id.trim();
    if (/^[1-9][0-9]{0,9}$/.test(trimmed)) {
      params.append('genreIds', trimmed);
    }
  }

  const numeric = ['yearFrom', 'yearTo', 'minRating', 'maxRating', 'minRuntime', 'maxRuntime'];
  for (const key of numeric) {
    const value = req.query[key];
    if (typeof value === 'string' && /^\d{1,4}(\.\d)?$/.test(value)) {
      params.set(key, value);
    }
  }

  if (typeof req.query.language === 'string' && /^[a-z]{2,3}$/.test(req.query.language)) {
    params.set('language', req.query.language);
  }

  try {
    const result = await backendRequest<PageResult<MovieSummary>>('/movies/filter?' + params, {}, 30000);
    res.status(200).json(result.data || []);
  } catch (error) {
    sendError(res, error);
  }
}

