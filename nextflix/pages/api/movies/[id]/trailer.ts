import { NextApiRequest, NextApiResponse } from 'next';
import { allowMethod, sendError } from '../../../../lib/api';
import { backendRequest } from '../../../../lib/backend';
import { Trailer } from '../../../../lib/movies';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'GET')) return;
  const id = req.query.id;
  if (typeof id !== 'string' || !/^[0-9a-fA-F-]{36}$/.test(id)) {
    res.status(400).json({ message: 'ID phim không hợp lệ' });
    return;
  }
  try {
    res.status(200).json(await backendRequest<Trailer>('/movies/' + id + '/trailer'));
  } catch (error) {
    sendError(res, error);
  }
}
