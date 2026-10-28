import { NextApiRequest, NextApiResponse } from 'next';
import { backendRequest } from './backend';
import { sendError } from './api';

// Wire contracts from RatingResponse / WatchHistoryResponse. Neither carries a year or an IMDb score
// (docs/backend-requests.md), so the ledger rows show the title only.
export type RatingItem = {
  id: number;
  movieId: number;
  movieTitle: string;
  moviePoster: string | null;
  rating: number;
  source?: string | null;
  createdAt: string;
};

export type HistoryItem = {
  id: number;
  movieId: number;
  title: string;
  posterPath: string | null;
  eventType?: string | null;
  progressSeconds?: number | null;
  createdAt: string;
};

export function pageParam(req: NextApiRequest, res: NextApiResponse): number | null {
  const page = Number(req.query.page || 1);
  if (Number.isSafeInteger(page) && page >= 1 && page <= 500) return page;
  res.status(400).json({ message: 'Invalid page number' });
  return null;
}

export function positiveId(value: string | string[] | undefined): number | null {
  if (typeof value !== 'string' || !/^[1-9][0-9]*$/.test(value) || !Number.isSafeInteger(Number(value))) return null;
  return Number(value);
}

// Calls a signed-in backend route with the session cookie; answers 401 itself when there is none.
export async function accountRequest<T>(req: NextApiRequest, res: NextApiResponse, path: string, method = 'GET',
  body?: unknown, signInMessage = 'Please sign in'): Promise<T | null> {
  const token = req.cookies.wtw_session;
  if (!token) {
    res.status(401).json({ message: signInMessage });
    return null;
  }
  try {
    return await backendRequest<T>(path, {
      method,
      headers: { Authorization: 'Bearer ' + token },
      ...(body === undefined ? {} : { body: JSON.stringify(body) })
    });
  } catch (error) {
    sendError(res, error);
    return null;
  }
}
