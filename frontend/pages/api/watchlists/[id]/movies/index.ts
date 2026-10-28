import { NextApiRequest, NextApiResponse } from 'next';
import { allowMethod } from '../../../../../lib/api';
import { pageParam } from '../../../../../lib/activity';
import { accountRequest, PageResult, signIn, visibleListId, WatchlistItem } from '../../../../../lib/watchlists';
import { MovieSummary } from '../../../../../lib/movies';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'GET')) return;
  const page = pageParam(req, res);
  if (!page) return;
  const id = await visibleListId(req, res);
  if (!id) return;
  const result = await accountRequest<PageResult<WatchlistItem>>(req, res, `/watchlists/${id}/movies?page=${page}&size=20`,
    'GET', undefined, signIn);
  if (result) res.status(200).json({ ...result, data: result.data.map((item): MovieSummary => item.movie) });
}
