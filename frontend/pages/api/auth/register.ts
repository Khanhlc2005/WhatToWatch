import { NextApiRequest, NextApiResponse } from 'next';
import { backendRequest } from '../../../lib/backend';
import { allowMethod, isCredentials, sendError } from '../../../lib/api';

type User = { id: string; email: string };

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'POST')) return;
  if (!isCredentials(req.body)) {
    res.status(400).json({ message: 'Email không hợp lệ hoặc mật khẩu dưới 8 ký tự' });
    return;
  }
  try {
    const user = await backendRequest<User>('/users', {
      method: 'POST',
      body: JSON.stringify(req.body)
    });
    res.status(201).json(user);
  } catch (error) {
    sendError(res, error);
  }
}
