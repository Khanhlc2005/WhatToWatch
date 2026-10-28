import { NextApiRequest, NextApiResponse } from 'next';
import { allowMethod, sendError } from '../../../lib/api';
import { positiveId } from '../../../lib/activity';
import { backendRequest } from '../../../lib/backend';
import { fetchVisibleLists, ListMembership, PageResult, WatchlistItem, WatchlistSummary } from '../../../lib/watchlists';

const PAGE_SIZE = 200;
const MAX_PAGES = 20;

async function holdsMovie(list: WatchlistSummary, movieId: number, token: string): Promise<boolean> {
  for (let page = 1; page <= MAX_PAGES && list.movieCount > 0; page++) {
    const items = await backendRequest<PageResult<WatchlistItem>>(`/watchlists/${list.id}/movies?page=${page}&size=${PAGE_SIZE}`,
      { headers: { Authorization: 'Bearer ' + token } });
    if (items.data.some(item => item.movie.id === movieId)) return true;
    if (page >= items.totalPages) break;
  }
  return false;
}

// There is no backend endpoint that says which named lists hold a movie (docs/backend-requests.md), so scan
// each list's items here until the movie is found. The lists are scanned in parallel.
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'GET')) return;
  const movieId = positiveId(req.query.movieId);
  if (!movieId) {
    res.status(400).json({ message: 'Invalid movie ID' });
    return;
  }
  const lists = await fetchVisibleLists(req, res);
  if (!lists) return;
  try {
    const token = req.cookies.wtw_session as string;
    const checked = await Promise.all(lists.map(list => holdsMovie(list, movieId, token)));
    const result: ListMembership[] = lists.map((list, index) => ({ id: list.id, name: list.name, count: list.movieCount, checked: checked[index] }));
    res.status(200).json(result);
  } catch (error) {
    sendError(res, error);
  }
}
