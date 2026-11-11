import { AnalysisResultSchema, type AnalysisResult } from '../lib/schema';

const TIMEOUT_MS = 90_000;

const ERROR_MESSAGES: Record<string, string> = {
  FILE_TOO_LARGE: 'The file is too large. The maximum size is 10 MB.',
  NOT_PDF: 'Choose a PDF file.',
  PDF_ENCRYPTED: 'This PDF is encrypted or password-protected.',
  PDF_INVALID: 'Could not read this PDF file. It may be damaged.',
  TOO_MANY_PAGES: 'The document has too many pages.',
  NO_TEXT: 'This PDF has no text layer (probably a scan). OCR is not supported.',
  RATE_LIMITED: 'Too many requests. Try again in a few minutes.',
  FORBIDDEN_ORIGIN: 'The server rejected this request.',
  AI_INVALID_OUTPUT: 'The AI model returned an invalid response. Try again.',
  AI_TIMEOUT: 'The analysis took too long. Try again.',
  AI_ERROR: 'The AI service is temporarily unavailable. Try again later.',
};

const NETWORK_MESSAGE = 'Could not connect to the server. Check your connection and try again.';
const FORMAT_MESSAGE = 'The server returned data in an unexpected format.';
const TIMEOUT_MESSAGE = 'The server did not respond within 90 seconds. Try again.';

const STATUS_MESSAGES: Record<number, string> = {
  413: 'The file is too large. The maximum size is 10 MB.',
  429: 'Too many requests. Try again in a few minutes.',
};

class ApiError extends Error {}

function messageFor(body: unknown, status: number): string {
  if (typeof body === 'object' && body !== null && 'error' in body) {
    const error = (body as { error?: { code?: unknown; message?: unknown } }).error;
    const known = typeof error?.code === 'string' ? ERROR_MESSAGES[error.code] : undefined;
    if (known) return known;
    if (typeof error?.message === 'string' && error.message) return error.message;
  }
  return STATUS_MESSAGES[status] ?? `The server returned an error (${status}).`;
}

export async function analyzePdf(file: File, signal?: AbortSignal): Promise<AnalysisResult> {
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
    let response: Response;
    try {
      response = await fetch(`${import.meta.env.VITE_API_URL}/api/analyze`, {
        method: 'POST',
        body,
        signal: controller.signal,
      });
    } catch (error) {
      if (timedOut) throw new ApiError(TIMEOUT_MESSAGE);
      if (signal?.aborted) throw error;
      throw new ApiError(NETWORK_MESSAGE);
    }

    let json: unknown;
    try {
      json = await response.json();
    } catch {
      throw new ApiError(response.ok ? FORMAT_MESSAGE : messageFor(null, response.status));
    }
    if (!response.ok) throw new ApiError(messageFor(json, response.status));

    const parsed = AnalysisResultSchema.safeParse(json);
    if (!parsed.success) throw new ApiError(FORMAT_MESSAGE);
    return parsed.data;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', onAbort);
  }
}
