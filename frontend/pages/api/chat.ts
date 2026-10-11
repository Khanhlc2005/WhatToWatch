import { NextApiRequest, NextApiResponse } from 'next';
import { allowMethod, sendError } from '../../lib/api';
import { backendRequest } from '../../lib/backend';

type ChatResult = {
  conversationId: number;
  reply: string;
  recommendedMovies: { movieId: string; title: string; reason: string }[];
};

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'POST')) return;
  const token = req.cookies.wtw_session;
  if (!token) return res.status(401).json({ message: 'Vui lòng đăng nhập để trò chuyện với AI' });

  const message = typeof req.body?.message === 'string' ? req.body.message.trim() : '';
  const conversationId = req.body?.conversationId;
  if (!message || message.length > 500 || (conversationId != null && (!Number.isSafeInteger(conversationId) || conversationId < 1))) {
    return res.status(400).json({ message: 'Nội dung trò chuyện không hợp lệ' });
  }

  try {
    const result = await backendRequest<ChatResult>('/chat', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token },
      body: JSON.stringify({ message, conversationId: conversationId || null })
    }, 400000);
    return res.status(200).json(result);
  } catch (error) {
    return sendError(res, error);
  }
}
