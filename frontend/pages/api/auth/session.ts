import { NextApiRequest, NextApiResponse } from 'next';
import { backendRequest } from '../../../lib/backend';
import { allowMethod } from '../../../lib/api';

// The backend only returns `valid`, so read the account email from the JWT subject (see docs/backend-requests.md).
function emailFromToken(token: string): string | null {
  try {
    const payload = JSON.parse(Buffer.from(token.split('.')[1] || '', 'base64').toString('utf8'));
    return typeof payload.sub === 'string' ? payload.sub : null;
  } catch {
    return null;
  }
}

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
    res.status(200).json({ authenticated: result.valid, ...(result.valid ? { email: emailFromToken(token) } : {}) });
  } catch {
    res.status(200).json({ authenticated: false });
  }
}
