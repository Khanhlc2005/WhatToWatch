import { NextApiRequest, NextApiResponse } from 'next';
import { libraryKind, libraryRequest } from '../../../../lib/library';
import { MovieSummary, PageResult } from '../../../../lib/movies';

type WatchlistItem = { id: number; movie: MovieSummary; addedAt: string };

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const kind = libraryKind(req, res);
  if (!kind) return;
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    res.status(405).json({ message: 'Phương thức không được hỗ trợ' });
    return;
  }
  const page = Number(req.query.page || 1);
  if (!Number.isSafeInteger(page) || page < 1 || page > 500) {
    res.status(400).json({ message: 'Số trang không hợp lệ' });
    return;
  }
  const path = (kind === 'favorites' ? '/favorites' : '/watchlists') + '?page=' + page + '&size=20';
  const result = await libraryRequest<PageResult<MovieSummary | WatchlistItem>>(req, res, path);
  if (!result) return;
  res.status(200).json({ ...result, data: kind === 'favorites' ? result.data : (result.data as WatchlistItem[]).map(item => item.movie) });
}
