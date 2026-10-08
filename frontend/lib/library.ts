import { NextApiRequest, NextApiResponse } from 'next';
import { backendRequest } from './backend';
import { sendError } from './api';

export type LibraryKind = 'favorites' | 'watchlist';

export function libraryKind(req: NextApiRequest, res: NextApiResponse): LibraryKind | null {
  if (req.query.kind === 'favorites' || req.query.kind === 'watchlist') return req.query.kind;
  res.status(404).json({ message: 'Danh sách không tồn tại' });
  return null;
}

export async function libraryRequest<T>(req: NextApiRequest, res: NextApiResponse, path: string, method = 'GET'): Promise<T | null> {
  const token = req.cookies.wtw_session;
  if (!token) {
    res.status(401).json({ message: 'Vui lòng đăng nhập để lưu phim' });
    return null;
  }
  try {
    return await backendRequest<T>(path, { method, headers: { Authorization: 'Bearer ' + token } });
  } catch (error) {
    sendError(res, error);
    return null;
  }
}
