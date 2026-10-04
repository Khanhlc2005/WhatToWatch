import { NextApiRequest, NextApiResponse } from 'next';
import { backendRequest } from '../../../lib/backend';
import { allowMethod, isCredentials, sendError } from '../../../lib/api';

type LoginResult = { token: string; authenticated: boolean };

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'POST')) return;
  if (!isCredentials(req.body)) {
    res.status(400).json({ message: 'Email hoặc mật khẩu không hợp lệ' });
    return;
  }
  try {
    const result = await backendRequest<LoginResult>('/auth/log-in', {
      method: 'POST',
      body: JSON.stringify(req.body)
    });
    if (!result.authenticated || !result.token) {
      res.status(401).json({ message: 'Đăng nhập không thành công' });
      return;
    }
    const secure = process.env.NODE_ENV === 'production' ? '; Secure' : '';
    res.setHeader('Set-Cookie', 'wtw_session=' + encodeURIComponent(result.token)
      + '; HttpOnly; SameSite=Lax; Path=/; Max-Age=3600' + secure);
    res.status(200).json({ authenticated: true });
  } catch (error) {
    sendError(res, error);
  }
}
