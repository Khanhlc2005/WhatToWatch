import { NextApiRequest, NextApiResponse } from 'next';
import { allowMethod } from '../../../lib/api';
import { accountRequest, pageParam, RatingItem } from '../../../lib/activity';
import { PageResult } from '../../../lib/movies';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'GET')) return;
  const page = pageParam(req, res);
  if (!page) return;
  const result = await accountRequest<PageResult<RatingItem>>(req, res, '/ratings/my-ratings?page=' + page + '&size=20',
    'GET', undefined, 'Please sign in to see your ratings');
  if (result) res.status(200).json(result);
}
