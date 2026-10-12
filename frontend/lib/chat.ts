import { NextApiRequest, NextApiResponse } from 'next';
import { backendRequest } from './backend';
import { sendError } from './api';

export type RecommendedMovie = { movie_id: string; title: string; reason: string };
export type ChatMessage = {
  id?: number;
  role: 'user' | 'assistant';
  content: string;
  recommendedMovies: RecommendedMovie[];
  createdAt?: string;
};
export type Conversation = { id: number; title: string; updatedAt: string };
export type ConversationDetail = { id: number; title: string; messages: ChatMessage[] };
export type ChatReply = {
  conversationId: number;
  status: 'answered' | 'no_match' | 'insufficient_context' | 'error';
  reply: string;
  recommendedMovies: RecommendedMovie[];
  createdAt: string;
};

export async function chatRequest<T>(
  req: NextApiRequest, res: NextApiResponse, path: string, method = 'GET', body?: unknown
): Promise<T | null> {
  const token = req.cookies.wtw_session;
  if (!token) {
    res.status(401).json({ message: 'Vui lòng đăng nhập để trò chuyện' });
    return null;
  }
  try {
    return await backendRequest<T>(path, {
      method,
      headers: { Authorization: 'Bearer ' + token },
      ...(body === undefined ? {} : { body: JSON.stringify(body) })
    }, method === 'POST' ? 270000 : 10000);
  } catch (error) {
    sendError(res, error);
    return null;
  }
}
