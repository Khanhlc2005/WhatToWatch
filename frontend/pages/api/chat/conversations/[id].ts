import { NextApiRequest, NextApiResponse } from 'next';
import { chatRequest, ConversationDetail } from '../../../../lib/chat';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET' && req.method !== 'DELETE') {
    res.setHeader('Allow', 'GET, DELETE');
    res.status(405).json({ message: 'Method not allowed' });
    return;
  }
  const id = Number(req.query.id);
  if (!Number.isSafeInteger(id) || id <= 0) {
    res.status(400).json({ message: 'Invalid conversation' });
    return;
  }
  const result = await chatRequest<ConversationDetail | string>(
    req, res, `/chat/conversations/${id}`, req.method
  );
  if (result) res.status(200).json(result);
}
