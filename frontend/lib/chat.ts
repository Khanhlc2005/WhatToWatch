import { NextApiRequest, NextApiResponse } from 'next';
import { backendRequest } from './backend';
import { sendError } from './api';

export type RecommendedMovie = { movie_id: string; title: string; reason: string };
export type ChatStatus = 'answered' | 'no_match' | 'insufficient_context' | 'error';
export type ChatMessage = {
  id?: number;
  role: 'user' | 'assistant';
  content: string;
  recommendedMovies: RecommendedMovie[];
  createdAt?: string;
  // Only present on a reply received in this session; stored messages do not carry it (docs/backend-requests.md).
  status?: ChatStatus;
};
export type Conversation = { id: number; title: string; updatedAt: string };
export type ConversationDetail = { id: number; title: string; messages: ChatMessage[] };
export type ChatReply = {
  conversationId: number;
  status: ChatStatus;
  reply: string;
  recommendedMovies: RecommendedMovie[];
  createdAt: string;
};

export async function chatRequest<T>(
  req: NextApiRequest, res: NextApiResponse, path: string, method = 'GET', body?: unknown
): Promise<T | null> {
  const token = req.cookies.wtw_session;
  if (!token) {
    res.status(401).json({ message: 'Please sign in to chat' });
    return null;
  }
  try {
    return await backendRequest<T>(path, {
      method,
      headers: { Authorization: 'Bearer ' + token },
      ...(body === undefined ? {} : { body: JSON.stringify(body) })
    }, method === 'POST' ? 400000 : 10000);
  } catch (error) {
    sendError(res, error);
    return null;
  }
}
