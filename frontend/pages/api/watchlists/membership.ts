import { NextApiRequest, NextApiResponse } from 'next';
import { allowMethod } from '../../../lib/api';
import { positiveId } from '../../../lib/activity';
import {
  accountRequest, fetchVisibleLists, ListMembership, PageResult, signIn, WatchlistItem
} from '../../../lib/watchlists';

const PAGE_SIZE = 200;
const MAX_PAGES = 20;

// There is no backend endpoint that says which named lists hold a movie (docs/backend-requests.md), so scan
// each list's items here until the movie is found.
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'GET')) return;
  const movieId = positiveId(req.query.movieId);
  if (!movieId) {
    res.status(400).json({ message: 'Invalid movie ID' });
    return;
  }
  const lists = await fetchVisibleLists(req, res);
  if (!lists) return;
  const result: ListMembership[] = [];
  for (const list of lists) {
    let checked = false;
    for (let page = 1; page <= MAX_PAGES && !checked && list.movieCount > 0; page++) {
      const items = await accountRequest<PageResult<WatchlistItem>>(req, res, `/watchlists/${list.id}/movies?page=${page}&size=${PAGE_SIZE}`,
        'GET', undefined, signIn);
      if (!items) return;
      checked = items.data.some(item => item.movie.id === movieId);
      if (page >= items.totalPages) break;
    }
    result.push({ id: list.id, name: list.name, count: list.movieCount, checked });
  }
  res.status(200).json(result);
}
