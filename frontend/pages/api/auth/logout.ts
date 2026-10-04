import { NextApiRequest, NextApiResponse } from 'next';
import { allowMethod } from '../../../lib/api';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'POST')) return;
  const secure = process.env.NODE_ENV === 'production' ? '; Secure' : '';
  res.setHeader('Set-Cookie', 'wtw_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0' + secure);
  res.status(200).json({ authenticated: false });
}
