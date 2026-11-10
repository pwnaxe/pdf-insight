import { AnalysisResultSchema, type AnalysisResult } from '../lib/schema';

const TIMEOUT_MS = 90_000;

const ERROR_MESSAGES: Record<string, string> = {
  FILE_TOO_LARGE: 'Plik jest za duży. Maksymalny rozmiar to 10 MB.',
  NOT_PDF: 'Wybierz plik w formacie PDF.',
  PDF_ENCRYPTED: 'Ten PDF jest zaszyfrowany lub chroniony hasłem.',
  PDF_INVALID: 'Nie udało się odczytać tego pliku PDF. Może być uszkodzony.',
  TOO_MANY_PAGES: 'Dokument ma zbyt wiele stron.',
  NO_TEXT: 'Ten PDF nie ma warstwy tekstowej (prawdopodobnie skan). OCR nie jest obsługiwany.',
  RATE_LIMITED: 'Zbyt wiele żądań. Spróbuj ponownie za kilka minut.',
  FORBIDDEN_ORIGIN: 'Serwer odrzucił to żądanie.',
  AI_INVALID_OUTPUT: 'Model AI zwrócił niepoprawną odpowiedź. Spróbuj ponownie.',
  AI_TIMEOUT: 'Analiza trwała zbyt długo. Spróbuj ponownie.',
  AI_ERROR: 'Usługa AI jest chwilowo niedostępna. Spróbuj ponownie później.',
};

const NETWORK_MESSAGE = 'Nie udało się połączyć z serwerem. Sprawdź połączenie i spróbuj ponownie.';
const FORMAT_MESSAGE = 'Serwer zwrócił dane w nieoczekiwanym formacie.';
const TIMEOUT_MESSAGE = 'Serwer nie odpowiedział w ciągu 90 sekund. Spróbuj ponownie.';

const STATUS_MESSAGES: Record<number, string> = {
  413: 'Plik jest za duży. Maksymalny rozmiar to 10 MB.',
  429: 'Zbyt wiele żądań. Spróbuj ponownie za kilka minut.',
};

export class ApiError extends Error {}

function messageFor(body: unknown, status: number): string {
  if (typeof body === 'object' && body !== null && 'error' in body) {
    const error = (body as { error?: { code?: unknown; message?: unknown } }).error;
    const known = typeof error?.code === 'string' ? ERROR_MESSAGES[error.code] : undefined;
    if (known) return known;
    if (typeof error?.message === 'string' && error.message) return error.message;
  }
  return STATUS_MESSAGES[status] ?? `Serwer zwrócił błąd (${status}).`;
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
