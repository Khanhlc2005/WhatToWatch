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

export async function backendRequest<T>(path: string, init: RequestInit = {}, timeoutMs = 10000,
  allowMissingResult = false): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(baseUrl + path, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init.headers },
      signal: controller.signal
    });
    let body: ApiEnvelope<T>;
    try {
      body = (await response.json()) as ApiEnvelope<T>;
    } catch {
      throw new BackendApiError(response.status === 401 || response.status === 403 ? 401 : 502,
        response.status === 401 || response.status === 403 ? 'Your session has expired' : 'Invalid backend response');
    }
    if (!response.ok || body.code !== 1000) {
      const status = body.code === 2001 || body.code === 2002 ? 404
        : body.code === 1002 ? 409
        : body.code === 1005 || body.code === 1004 ? 401
        : response.status;
      throw new BackendApiError(status, body.message || 'Request failed');
    }
    if (body.result === undefined && !allowMissingResult) throw new BackendApiError(502, 'Backend response is missing data');
    if (body.result === undefined) return null as unknown as T;
    return body.result;
  } catch (error) {
    if (error instanceof BackendApiError) throw error;
    if (controller.signal.aborted) throw new BackendApiError(504, 'The request timed out. Please try again');
    throw new BackendApiError(502, 'Could not connect to the backend');
  } finally {
    clearTimeout(timeout);
  }
}
