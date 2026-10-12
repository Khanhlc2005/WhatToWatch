import { NextApiRequest, NextApiResponse } from 'next';
import { backendRequest } from '../../../lib/backend';
import { sendError } from '../../../lib/api';

type RatingResult = { movieId: number; rating: number } | null;

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET' && req.method !== 'POST') {
    res.setHeader('Allow', 'GET, POST');
    res.status(405).json({ message: 'Method not allowed' });
    return;
  }
  const movieId = req.query.movieId;
  if (typeof movieId !== 'string' || !/^[1-9][0-9]*$/.test(movieId) || !Number.isSafeInteger(Number(movieId))) {
    res.status(400).json({ message: 'Invalid movie ID' });
    return;
  }
  const token = req.cookies.wtw_session;
  if (!token) {
    res.status(401).json({ message: 'Please sign in to rate movies' });
    return;
  }
  if (req.method === 'POST' && (!Number.isInteger(req.body?.rating) || req.body.rating < 1 || req.body.rating > 5)) {
    res.status(400).json({ message: 'Rating must be between 1 and 5' });
    return;
  }
  try {
    const path = req.method === 'GET' ? '/ratings/movie/' + movieId : '/ratings';
    const result = await backendRequest<RatingResult>(path, {
      method: req.method,
      headers: { Authorization: 'Bearer ' + token },
      ...(req.method === 'POST' ? { body: JSON.stringify({ movieId: Number(movieId), rating: req.body.rating }) } : {})
    }, 10000, req.method === 'GET');
    res.status(200).json(result);
  } catch (error) {
    sendError(res, error);
  }
}
