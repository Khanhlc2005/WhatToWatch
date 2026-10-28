import { NextApiRequest, NextApiResponse } from 'next';
import { allowMethod } from '../../../lib/api';
import { accountRequest, positiveId } from '../../../lib/activity';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'DELETE')) return;
  const id = positiveId(req.query.id);
  if (!id) {
    res.status(400).json({ message: 'Invalid history ID' });
    return;
  }
  const result = await accountRequest<string>(req, res, '/watch-history/' + id, 'DELETE', undefined,
    'Please sign in to use your watch history');
  if (result !== null) res.status(200).json({ message: result });
}
