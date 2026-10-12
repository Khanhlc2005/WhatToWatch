import { NextApiRequest, NextApiResponse } from 'next';
import { allowMethod } from '../../../lib/api';
import { chatRequest, ChatReply } from '../../../lib/chat';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'POST')) return;
  const body = req.body as Record<string, unknown> | null;
  if (!body || typeof body.message !== 'string' || !body.message.trim() || body.message.length > 2000 ||
    (body.conversationId !== undefined && body.conversationId !== null &&
      (typeof body.conversationId !== 'number' || !Number.isSafeInteger(body.conversationId) || body.conversationId <= 0))) {
    res.status(400).json({ message: 'Tin nhắn hoặc cuộc hội thoại không hợp lệ' });
    return;
  }
  const result = await chatRequest<ChatReply>(req, res, '/chat', 'POST', {
    message: body.message.trim(), conversationId: body.conversationId || null
  });
  if (result) res.status(200).json(result);
}
