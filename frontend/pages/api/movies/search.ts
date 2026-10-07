import { NextApiRequest, NextApiResponse } from 'next';
import { allowMethod, sendError } from '../../../lib/api';
import { backendRequest } from '../../../lib/backend';
import { MovieSummary, PageResult } from '../../../lib/movies';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'GET')) return;
  const query = req.query.q;
  const page = Number(req.query.page || 0);
  if (typeof query !== 'string' || !query.trim() || query.length > 100 ||
      !Number.isSafeInteger(page) || page < 0 || page > 500) {
    res.status(400).json({ message: 'Từ khóa tìm kiếm không hợp lệ' });
    return;
  }
  try {
    const params = new URLSearchParams({ query: query.trim(), page: String(page), size: '20' });
    res.status(200).json(await backendRequest<PageResult<MovieSummary>>('/movies/search?' + params));
  } catch (error) {
    sendError(res, error);
  }
}
