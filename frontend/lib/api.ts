import { NextApiRequest, NextApiResponse } from 'next';
import { BackendApiError } from './backend';

export function allowMethod(req: NextApiRequest, res: NextApiResponse, method: string): boolean {
  if (req.method === method) return true;
  res.setHeader('Allow', method);
  res.status(405).json({ message: 'Phương thức không được hỗ trợ' });
  return false;
}

export function sendError(res: NextApiResponse, error: unknown): void {
  if (error instanceof BackendApiError) {
    res.status(error.status).json({ message: error.message });
    return;
  }
  res.status(500).json({ message: 'Lỗi máy chủ' });
}

export function isCredentials(value: unknown): value is { email: string; password: string } {
  if (!value || typeof value !== 'object') return false;
  const body = value as Record<string, unknown>;
  return typeof body.email === 'string' && typeof body.password === 'string'
    && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(body.email)
    && body.password.length >= 8;
}
