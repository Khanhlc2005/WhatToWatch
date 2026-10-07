import { NextApiRequest, NextApiResponse } from 'next';
import { libraryKind, libraryRequest } from '../../../../lib/library';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const kind = libraryKind(req, res);
  if (!kind) return;
  const id = req.query.movieId;
  if (typeof id !== 'string' || !/^[1-9][0-9]*$/.test(id) || !Number.isSafeInteger(Number(id))) {
    res.status(400).json({ message: 'ID phim không hợp lệ' });
    return;
  }
  if (!['GET', 'POST', 'DELETE'].includes(req.method || '')) {
    res.setHeader('Allow', 'GET, POST, DELETE');
    res.status(405).json({ message: 'Phương thức không được hỗ trợ' });
    return;
  }
  const base = kind === 'favorites' ? '/favorites' : '/watchlists';
  const path = req.method === 'GET' ? base + '/status?movieId=' + id
    : kind === 'favorites' ? base + '/' + id : base + '/movies/' + id;
  const result = await libraryRequest<unknown>(req, res, path, req.method);
  if (result !== null) res.status(200).json(result);
}
