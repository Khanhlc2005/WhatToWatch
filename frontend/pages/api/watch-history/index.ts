import { NextApiRequest, NextApiResponse } from 'next';
import { accountRequest, HistoryItem, pageParam, positiveId } from '../../../lib/activity';
import { PageResult } from '../../../lib/movies';

const message = 'Please sign in to use your watch history';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    const page = pageParam(req, res);
    if (!page) return;
    const result = await accountRequest<PageResult<HistoryItem>>(req, res, '/watch-history?page=' + page + '&size=20',
      'GET', undefined, message);
    if (result !== null) res.status(200).json(result);
    return;
  }
  if (req.method === 'POST') {
    const movieId = typeof req.body?.movieId === 'number' ? req.body.movieId : null;
    if (movieId === null || !positiveId(String(movieId))) {
      res.status(400).json({ message: 'Invalid movie ID' });
      return;
    }
    const result = await accountRequest<HistoryItem>(req, res, '/watch-history', 'POST', { movieId }, message);
    if (result !== null) res.status(200).json(result);
    return;
  }
  if (req.method === 'DELETE') {
    const result = await accountRequest<string>(req, res, '/watch-history', 'DELETE', undefined, message);
    if (result !== null) res.status(200).json({ message: result });
    return;
  }
  res.setHeader('Allow', 'GET, POST, DELETE');
  res.status(405).json({ message: 'Method not allowed' });
}
