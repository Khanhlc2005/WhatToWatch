import { NextApiRequest, NextApiResponse } from 'next';
import { backendRequest } from '../../../lib/backend';
import { allowMethod } from '../../../lib/api';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'GET')) return;
  const token = req.cookies.wtw_session;
  if (!token) {
    res.status(200).json({ authenticated: false });
    return;
  }
  try {
    const result = await backendRequest<{ valid: boolean }>('/auth/introspect', {
      method: 'POST',
      body: JSON.stringify({ token })
    });
    res.status(200).json({ authenticated: result.valid });
  } catch {
    res.status(200).json({ authenticated: false });
  }
}
