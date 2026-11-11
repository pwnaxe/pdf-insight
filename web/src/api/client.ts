import { dictionary, type Lang, type Messages } from '../lib/i18n';
import { AnalysisResultSchema, type AnalysisResult } from '../lib/schema';

const TIMEOUT_MS = 90_000;

class ApiError extends Error {}

function messageFor(t: Messages, body: unknown, status: number): string {
  if (typeof body === 'object' && body !== null && 'error' in body) {
    const error = (body as { error?: { code?: unknown; message?: unknown } }).error;
    if (typeof error?.code === 'string' && Object.hasOwn(t.errors, error.code)) {
      return t.errors[error.code as keyof Messages['errors']];
    }
    // the API words its own messages in the requested language
    if (typeof error?.message === 'string' && error.message) return error.message;
  }
  if (status === 413) return t.errors.FILE_TOO_LARGE;
  if (status === 429) return t.errors.RATE_LIMITED;
  return t.httpError(status);
}

export async function analyzePdf(
  file: File,
  lang: Lang,
  signal?: AbortSignal,
): Promise<AnalysisResult> {
  const t = dictionary[lang];
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, TIMEOUT_MS);
  const onAbort = () => controller.abort();
  signal?.addEventListener('abort', onAbort);

  try {
    const body = new FormData();
    body.append('file', file);
    body.append('lang', lang);
    let response: Response;
    try {
      response = await fetch(`${import.meta.env.VITE_API_URL}/api/analyze`, {
        method: 'POST',
        body,
        signal: controller.signal,
      });
    } catch (error) {
      if (timedOut) throw new ApiError(t.timeout);
      if (signal?.aborted) throw error;
      throw new ApiError(t.network);
    }

    let json: unknown;
    try {
      json = await response.json();
    } catch {
      throw new ApiError(response.ok ? t.badFormat : messageFor(t, null, response.status));
    }
    if (!response.ok) throw new ApiError(messageFor(t, json, response.status));

    const parsed = AnalysisResultSchema.safeParse(json);
    if (!parsed.success) throw new ApiError(t.badFormat);
    return parsed.data;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', onAbort);
  }
}
