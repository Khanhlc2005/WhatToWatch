import { NextApiRequest, NextApiResponse } from 'next';
import { backendRequest } from '../../../lib/backend';
import { allowMethod, sendError } from '../../../lib/api';
import { RecommendationResult } from '../../../lib/recommendations';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'GET')) return;
  const token = req.cookies.wtw_session;
  if (!token) {
    res.status(401).json({ message: 'Please sign in to see your recommendations' });
    return;
  }
  try {
    const result = await backendRequest<RecommendationResult>('/movies/recommendations?limit=10', {
      headers: { Authorization: 'Bearer ' + token }
    }, 120000);
    res.status(200).json(result);
  } catch (error) {
    sendError(res, error);
  }
}
