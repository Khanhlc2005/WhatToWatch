import { NextApiRequest, NextApiResponse } from 'next';
import {
  accountRequest, DEFAULT_LIST_NAME, fetchAllLists, fetchVisibleLists, isDefaultList, listNameParam, signIn, WatchlistSummary
} from '../../../lib/watchlists';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    const lists = await fetchVisibleLists(req, res);
    if (lists) res.status(200).json(lists);
    return;
  }
  if (req.method === 'POST') {
    const name = listNameParam(req, res);
    if (!name) return;
    const all = await fetchAllLists(req, res);
    if (!all) return;
    // With two or more lists and no list named "Default Watchlist", the backend cannot pick the Watch later list
    // and fails (docs/backend-requests.md), so make sure that list exists before adding a named one.
    if (!all.some(isDefaultList)) {
      const created = await accountRequest<WatchlistSummary>(req, res, '/watchlists', 'POST', { name: DEFAULT_LIST_NAME }, signIn);
      if (!created) return;
    }
    const list = await accountRequest<WatchlistSummary>(req, res, '/watchlists', 'POST', { name }, signIn);
    if (list) res.status(201).json(list);
    return;
  }
  res.setHeader('Allow', 'GET, POST');
  res.status(405).json({ message: 'Method not allowed' });
}
