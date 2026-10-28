import { NextApiRequest, NextApiResponse } from 'next';
import { allowMethod, sendError } from '../../lib/api';
import { backendRequest } from '../../lib/backend';
import { MovieSummary, PageResult } from '../../lib/movies';
import { GENRE_FILTER_ENABLED, RATING_FILTER_ENABLED } from '../../config/features';

const numeric = ['yearFrom', 'yearTo', 'minRuntime', 'maxRuntime', ...(RATING_FILTER_ENABLED ? ['minRating', 'maxRating'] : [])];

// GET /movies/filter. The page is 1-based here; the backend's Pageable is 0-based.
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'GET')) return;
  const params = new URLSearchParams();
  const page = Number(req.query.page || 1);
  if (!Number.isSafeInteger(page) || page < 1 || page > 500) {
    res.status(400).json({ message: 'Invalid page number' });
    return;
  }
  const genres = typeof req.query.genreIds === 'string' && req.query.genreIds ? req.query.genreIds.split(',') : [];
  if (genres.length > 30 || genres.some(id => !/^[1-9][0-9]{0,9}$/.test(id))) {
    res.status(400).json({ message: 'Invalid genres' });
    return;
  }
  if (GENRE_FILTER_ENABLED) genres.forEach(id => params.append('genreIds', id));
  for (const key of numeric) {
    const value = req.query[key];
    if (value === undefined || value === '') continue;
    if (typeof value !== 'string' || !/^\d{1,4}(\.\d)?$/.test(value)) {
      res.status(400).json({ message: 'Invalid ' + key });
      return;
    }
    params.set(key, value);
  }
  for (const [low, high] of [['yearFrom', 'yearTo'], ['minRuntime', 'maxRuntime'], ['minRating', 'maxRating']]) {
    const from = params.get(low);
    const to = params.get(high);
    if (from !== null && to !== null && Number(from) > Number(to)) {
      res.status(400).json({ message: `${low} must not be greater than ${high}` });
      return;
    }
  }
  const language = req.query.language;
  if (typeof language === 'string' && language) {
    if (!/^[a-z]{2,3}$/.test(language)) {
      res.status(400).json({ message: 'Invalid language' });
      return;
    }
    params.set('language', language);
  }
  params.set('page', String(page - 1));
  params.set('size', '20');
  try {
    res.status(200).json(await backendRequest<PageResult<MovieSummary>>('/movies/filter?' + params, {}, 30000));
  } catch (error) {
    sendError(res, error);
  }
}
