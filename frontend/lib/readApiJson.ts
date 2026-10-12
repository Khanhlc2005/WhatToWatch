export async function readApiJson<T>(response: Response, fallbackMessage: string, allowEmpty = false): Promise<T> {
  const text = await response.text();
  if (!text.trim()) {
    if (allowEmpty && response.ok) return null as unknown as T;
    throw new Error(fallbackMessage);
  }
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error(fallbackMessage);
  }
}
