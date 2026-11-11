import { createContext, createElement, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

export type Lang = 'pl' | 'en';

export const LANGS: readonly Lang[] = ['pl', 'en'];
export const DEFAULT_LANG: Lang = 'pl';
export const LANG_STORAGE_KEY = 'pdf-insight:lang';

const LOCALES: Record<Lang, string> = { pl: 'pl-PL', en: 'en-GB' };

const en = {
  appTitle: 'PDF Insight',
  tagline: 'Upload a PDF document to get its summary, amounts and dates.',
  languageLabel: 'Language',
  aiNotice:
    'The file is sent to our server, and its text is sent to an external AI model API (OpenAI) for analysis. We do not store files. Do not upload documents containing sensitive data.',
  dropAria: 'Upload a PDF file',
  dropTitle: 'Drag a PDF file here or',
  chooseFile: 'Choose file',
  dropHint: 'PDF with a text layer, up to 10 MB.',
  empty: 'Upload a PDF document to see its summary, amounts, dates and key points.',
  tryAgain: 'Try again',
  chooseAnother: 'Choose another file',
  history: 'History',
  noHistory: 'No saved analyses.',
  clearHistory: 'Clear history',
  open: 'Open',
  delete: 'Delete',
  deleteAria: (name: string) => `Delete ${name}`,
  uploading: 'Uploading file…',
  analysing: 'Analysing document…',
  seconds: (n: number) => `${n} s`,
  analysisResult: 'Analysis result',
  type: 'Type',
  language: 'Language',
  date: 'Date',
  pages: 'Pages',
  file: 'File',
  none: 'None',
  noDate: 'none',
  summary: 'Summary',
  warnings: 'Warnings',
  keyPoints: 'Key points',
  entities: 'Entities',
  organizations: 'Organizations',
  people: 'People',
  amounts: 'Amounts',
  amount: 'Amount',
  context: 'Context',
  dates: 'Dates',
  keywords: 'Keywords',
  json: 'JSON',
  downloadJson: 'Download JSON',
  copyJson: 'Copy JSON',
  previewJson: 'Preview JSON',
  copied: 'Copied.',
  copyFailed: 'Could not copy.',
  injectionTitle: 'Suspicious content detected.',
  injectionBody:
    'The document contains text that looks like instructions for an AI system. It was ignored, but treat the results with care.',
  validation: {
    notPdf: 'Choose a PDF file.',
    empty: 'This file is empty.',
    tooLarge: 'The file is too large. The maximum size is 10 MB.',
    badSignature: 'This file does not look like a valid PDF document.',
  },
  errors: {
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
  },
  network: 'Could not connect to the server. Check your connection and try again.',
  badFormat: 'The server returned data in an unexpected format.',
  timeout: 'The server did not respond within 90 seconds. Try again.',
  httpError: (status: number) => `The server returned an error (${status}).`,
  unexpected: 'An unexpected error occurred.',
};

type Widen<T> = {
  [K in keyof T]: T[K] extends (...args: infer A) => string
    ? (...args: A) => string
    : T[K] extends string
      ? string
      : Widen<T[K]>;
};

export type Messages = Widen<typeof en>;

const pl: Messages = {
  appTitle: 'PDF Insight',
  tagline: 'Wgraj dokument PDF, aby zobaczyć jego streszczenie, kwoty i daty.',
  languageLabel: 'Język',
  aiNotice:
    'Plik jest wysyłany na nasz serwer, a jego tekst do zewnętrznego API modelu AI (OpenAI) w celu analizy. Nie przechowujemy plików. Nie wgrywaj dokumentów z danymi wrażliwymi.',
  dropAria: 'Wgraj plik PDF',
  dropTitle: 'Przeciągnij plik PDF tutaj lub',
  chooseFile: 'Wybierz plik',
  dropHint: 'PDF z warstwą tekstową, do 10 MB.',
  empty: 'Wgraj dokument PDF, aby zobaczyć jego streszczenie, kwoty, daty i najważniejsze punkty.',
  tryAgain: 'Spróbuj ponownie',
  chooseAnother: 'Wybierz inny plik',
  history: 'Historia',
  noHistory: 'Brak zapisanych analiz.',
  clearHistory: 'Wyczyść historię',
  open: 'Otwórz',
  delete: 'Usuń',
  deleteAria: (name) => `Usuń ${name}`,
  uploading: 'Wysyłanie pliku…',
  analysing: 'Analizowanie dokumentu…',
  seconds: (n) => `${n} s`,
  analysisResult: 'Wynik analizy',
  type: 'Typ',
  language: 'Język',
  date: 'Data',
  pages: 'Strony',
  file: 'Plik',
  none: 'Brak',
  noDate: 'brak',
  summary: 'Streszczenie',
  warnings: 'Ostrzeżenia',
  keyPoints: 'Najważniejsze punkty',
  entities: 'Podmioty',
  organizations: 'Organizacje',
  people: 'Osoby',
  amounts: 'Kwoty',
  amount: 'Kwota',
  context: 'Kontekst',
  dates: 'Daty',
  keywords: 'Słowa kluczowe',
  json: 'JSON',
  downloadJson: 'Pobierz JSON',
  copyJson: 'Kopiuj JSON',
  previewJson: 'Podgląd JSON',
  copied: 'Skopiowano.',
  copyFailed: 'Nie udało się skopiować.',
  injectionTitle: 'Wykryto podejrzaną treść.',
  injectionBody:
    'Dokument zawiera tekst przypominający polecenia dla systemu AI. Został zignorowany, ale potraktuj wyniki z ostrożnością.',
  validation: {
    notPdf: 'Wybierz plik PDF.',
    empty: 'Ten plik jest pusty.',
    tooLarge: 'Plik jest za duży. Maksymalny rozmiar to 10 MB.',
    badSignature: 'Ten plik nie wygląda na prawidłowy dokument PDF.',
  },
  errors: {
    FILE_TOO_LARGE: 'Plik jest za duży. Maksymalny rozmiar to 10 MB.',
    NOT_PDF: 'Wybierz plik PDF.',
    PDF_ENCRYPTED: 'Ten plik PDF jest zaszyfrowany lub chroniony hasłem.',
    PDF_INVALID: 'Nie udało się odczytać tego pliku PDF. Może być uszkodzony.',
    TOO_MANY_PAGES: 'Dokument ma zbyt wiele stron.',
    NO_TEXT: 'Ten PDF nie ma warstwy tekstowej (prawdopodobnie to skan). OCR nie jest obsługiwany.',
    RATE_LIMITED: 'Zbyt wiele żądań. Spróbuj ponownie za kilka minut.',
    FORBIDDEN_ORIGIN: 'Serwer odrzucił to żądanie.',
    AI_INVALID_OUTPUT: 'Model AI zwrócił nieprawidłową odpowiedź. Spróbuj ponownie.',
    AI_TIMEOUT: 'Analiza trwała zbyt długo. Spróbuj ponownie.',
    AI_ERROR: 'Usługa AI jest chwilowo niedostępna. Spróbuj ponownie później.',
  },
  network: 'Nie udało się połączyć z serwerem. Sprawdź połączenie i spróbuj ponownie.',
  badFormat: 'Serwer zwrócił dane w nieoczekiwanym formacie.',
  timeout: 'Serwer nie odpowiedział w ciągu 90 sekund. Spróbuj ponownie.',
  httpError: (status) => `Serwer zwrócił błąd (${status}).`,
  unexpected: 'Wystąpił nieoczekiwany błąd.',
};

export const dictionary: Record<Lang, Messages> = { pl, en };

export function parseLang(value: unknown): Lang {
  return value === 'en' || value === 'pl' ? value : DEFAULT_LANG;
}

export function localeFor(lang: Lang): string {
  return LOCALES[lang];
}

function readStoredLang(): Lang {
  try {
    return parseLang(localStorage.getItem(LANG_STORAGE_KEY));
  } catch {
    return DEFAULT_LANG;
  }
}

type I18n = { lang: Lang; setLang: (lang: Lang) => void; t: Messages };

const I18nContext = createContext<I18n | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(readStoredLang);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const value = useMemo<I18n>(
    () => ({
      lang,
      t: dictionary[lang],
      setLang: (next) => {
        try {
          localStorage.setItem(LANG_STORAGE_KEY, next);
        } catch {
          // private mode: the choice then lasts only for this session
        }
        setLangState(next);
      },
    }),
    [lang],
  );

  return createElement(I18nContext.Provider, { value }, children);
}

export function useI18n(): I18n {
  const value = useContext(I18nContext);
  if (!value) throw new Error('useI18n must be used inside I18nProvider');
  return value;
}
