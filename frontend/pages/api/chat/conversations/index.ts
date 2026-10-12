import { NextApiRequest, NextApiResponse } from 'next';
import { allowMethod } from '../../../../lib/api';
import { chatRequest, Conversation } from '../../../../lib/chat';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'GET')) return;
  const result = await chatRequest<Conversation[]>(req, res, '/chat/conversations');
  if (result) res.status(200).json(result);
}
