import { NextApiRequest, NextApiResponse } from 'next';
import { accountRequest, positiveId } from './activity';
import { MovieSummary, PageResult } from './movies';

// Wire contracts from WatchlistResponse / WatchlistItemResponse.
export type WatchlistSummary = { id: number; name: string; movieCount: number; createdAt: string };
export type WatchlistItem = { id: number; movie: MovieSummary; addedAt: string };
export type ListMembership = { id: number; name: string; count: number; checked: boolean };

// The backend keeps "Watch later" as a normal list with this name and returns it from GET /watchlists/lists,
// where it can also be renamed or deleted (docs/backend-requests.md). The UI hides it and refuses the name.
export const DEFAULT_LIST_NAME = 'Default Watchlist';
export const LIST_NAME_MAX = 60;

export function isDefaultList(list: Pick<WatchlistSummary, 'name'>): boolean {
  return list.name.trim().toLowerCase() === DEFAULT_LIST_NAME.toLowerCase();
}

// Returns the cleaned name, or null after answering 400.
export function listNameParam(req: NextApiRequest, res: NextApiResponse): string | null {
  const name = typeof req.body?.name === 'string' ? req.body.name.trim() : '';
  if (!name || name.length > LIST_NAME_MAX) {
    res.status(400).json({ message: `Enter a list name of up to ${LIST_NAME_MAX} characters.` });
    return null;
  }
  if (name.toLowerCase() === DEFAULT_LIST_NAME.toLowerCase()) {
    res.status(400).json({ message: 'That name is reserved. Choose another name.' });
    return null;
  }
  return name;
}

const signIn = 'Please sign in to use your lists';

export async function fetchAllLists(req: NextApiRequest, res: NextApiResponse): Promise<WatchlistSummary[] | null> {
  return accountRequest<WatchlistSummary[]>(req, res, '/watchlists/lists', 'GET', undefined, signIn);
}

// The user's own lists, without the hidden Watch later list.
export async function fetchVisibleLists(req: NextApiRequest, res: NextApiResponse): Promise<WatchlistSummary[] | null> {
  const lists = await fetchAllLists(req, res);
  return lists && lists.filter(list => !isDefaultList(list));
}

// Checks that `?id=` is one of the user's visible lists, so the hidden list cannot be renamed or deleted here.
export async function visibleListId(req: NextApiRequest, res: NextApiResponse): Promise<number | null> {
  const id = positiveId(req.query.id);
  if (!id) {
    res.status(400).json({ message: 'Invalid list ID' });
    return null;
  }
  const lists = await fetchVisibleLists(req, res);
  if (!lists) return null;
  if (!lists.some(list => list.id === id)) {
    res.status(404).json({ message: 'List not found' });
    return null;
  }
  return id;
}

export { accountRequest, signIn };
export type { PageResult };
