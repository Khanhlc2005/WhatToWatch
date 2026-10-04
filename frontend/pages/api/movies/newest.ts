import { NextApiRequest, NextApiResponse } from 'next';
import { allowMethod, sendError } from '../../../lib/api';
import { backendRequest } from '../../../lib/backend';
import { MovieSummary } from '../../../lib/movies';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'GET')) return;
  try {
    res.status(200).json(await backendRequest<MovieSummary[]>('/movies/home-feed/newest'));
  } catch (error) {
    sendError(res, error);
  }
}
