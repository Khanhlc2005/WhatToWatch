import { NextApiRequest, NextApiResponse } from 'next';
import { positiveId } from '../../../../../lib/activity';
import { accountRequest, signIn, visibleListId } from '../../../../../lib/watchlists';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST' && req.method !== 'DELETE') {
    res.setHeader('Allow', 'POST, DELETE');
    res.status(405).json({ message: 'Method not allowed' });
    return;
  }
  const movieId = positiveId(req.query.movieId);
  if (!movieId) {
    res.status(400).json({ message: 'Invalid movie ID' });
    return;
  }
  const id = await visibleListId(req, res);
  if (!id) return;
  const result = await accountRequest<string>(req, res, `/watchlists/${id}/movies/${movieId}`, req.method, undefined, signIn);
  if (result !== null) res.status(200).json({ message: result });
}
