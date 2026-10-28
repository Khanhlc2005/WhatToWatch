import { NextApiRequest, NextApiResponse } from 'next';
import { accountRequest, listNameParam, signIn, visibleListId, WatchlistSummary } from '../../../../lib/watchlists';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'PUT' && req.method !== 'DELETE') {
    res.setHeader('Allow', 'PUT, DELETE');
    res.status(405).json({ message: 'Method not allowed' });
    return;
  }
  const name = req.method === 'PUT' ? listNameParam(req, res) : '';
  if (name === null) return;
  const id = await visibleListId(req, res);
  if (!id) return;
  if (req.method === 'PUT') {
    const list = await accountRequest<WatchlistSummary>(req, res, '/watchlists/' + id, 'PUT', { name }, signIn);
    if (list) res.status(200).json(list);
    return;
  }
  const result = await accountRequest<string>(req, res, '/watchlists/' + id, 'DELETE', undefined, signIn);
  if (result !== null) res.status(200).json({ message: result });
}
