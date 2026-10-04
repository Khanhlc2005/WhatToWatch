export type ApiEnvelope<T> = {
  code: number;
  message?: string;
  result?: T;
};

export class BackendApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

const baseUrl = (process.env.BACKEND_URL || 'http://localhost:8080/movie-recommendation').replace(/\/$/, '');

export async function backendRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(baseUrl + path, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init.headers },
      signal: controller.signal
    });
    const body = (await response.json()) as ApiEnvelope<T>;
    if (!response.ok || body.code !== 1000) {
      const status = body.code === 2001 || body.code === 2002 ? 404
        : body.code === 1002 ? 409
        : body.code === 1005 || body.code === 1004 ? 401
        : response.status;
      throw new BackendApiError(status, body.message || 'Yêu cầu không thành công');
    }
    if (body.result === undefined) throw new BackendApiError(502, 'Phản hồi backend thiếu dữ liệu');
    return body.result;
  } catch (error) {
    if (error instanceof BackendApiError) throw error;
    throw new BackendApiError(502, 'Không kết nối được backend');
  } finally {
    clearTimeout(timeout);
  }
}
