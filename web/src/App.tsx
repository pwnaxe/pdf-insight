import { useCallback, useReducer, useRef, useState } from 'react';
import { analyzePdf } from './api/client';
import { LanguageToggle } from './components/LanguageToggle';
import { Dropzone } from './components/Dropzone';
import { EmptyState } from './components/EmptyState';
import { ErrorState } from './components/ErrorState';
import { HistoryPanel } from './components/HistoryPanel';
import { LoadingState } from './components/LoadingState';
import { AiNotice } from './components/AiNotice';
import { ResultView } from './components/ResultView';
import {
  addToHistory,
  clearHistory,
  loadHistory,
  removeFromHistory,
  type HistoryEntry,
} from './lib/history';
import { useI18n } from './lib/i18n';
import type { AnalysisResult } from './lib/schema';
import { validateFile } from './lib/validateFile';

type State =
  | { status: 'idle' }
  | { status: 'uploading'; file: File }
  | { status: 'done'; result: AnalysisResult }
  | { status: 'error'; message: string; file: File | null };

type Action =
  | { type: 'start'; file: File }
  | { type: 'success'; result: AnalysisResult }
  | { type: 'failure'; message: string; file: File | null }
  | { type: 'reset' };

function reducer(_state: State, action: Action): State {
  switch (action.type) {
    case 'start':
      return { status: 'uploading', file: action.file };
    case 'success':
      return { status: 'done', result: action.result };
    case 'failure':
      return { status: 'error', message: action.message, file: action.file };
    case 'reset':
      return { status: 'idle' };
  }
}

export default function App() {
  const { lang, t } = useI18n();
  const [state, dispatch] = useReducer(reducer, { status: 'idle' });
  const [history, setHistory] = useState<HistoryEntry[]>(() => loadHistory());
  const controllerRef = useRef<AbortController | null>(null);

  const analyze = useCallback(
    async (file: File) => {
      controllerRef.current?.abort();
      const controller = new AbortController();
      controllerRef.current = controller;
      dispatch({ type: 'start', file });
      try {
        const result = await analyzePdf(file, lang, controller.signal);
        if (controller.signal.aborted) return;
        setHistory(addToHistory(result));
        dispatch({ type: 'success', result });
      } catch (error) {
        if (controller.signal.aborted) return;
        const message = error instanceof Error ? error.message : t.unexpected;
        dispatch({ type: 'failure', message, file });
      }
    },
    [lang, t],
  );

  const onFile = useCallback(
    async (file: File) => {
      const problem = await validateFile(file, t);
      if (problem) {
        controllerRef.current?.abort();
        dispatch({ type: 'failure', message: problem, file: null });
        return;
      }
      await analyze(file);
    },
    [analyze, t],
  );

  const reset = () => {
    controllerRef.current?.abort();
    dispatch({ type: 'reset' });
  };

  const openEntry = (entry: HistoryEntry) => {
    controllerRef.current?.abort();
    dispatch({ type: 'success', result: entry.result });
    window.scrollTo({ top: 0 });
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 px-4 py-8 sm:px-6 sm:py-12">
      <header className="flex items-center justify-between gap-3 border-b-2 border-ink-900 pb-4">
        <div className="flex min-w-0 items-center gap-2.5">
          <span aria-hidden="true" className="size-3.5 shrink-0 bg-accent-500" />
          <h1 className="font-mono text-xl font-bold tracking-tight text-ink-950">{t.appTitle}</h1>
        </div>
        <LanguageToggle />
      </header>
      <p className="max-w-prose text-lg text-ink-700">{t.tagline}</p>
      <main className="flex flex-col gap-6">
        <AiNotice />

        <Dropzone disabled={state.status === 'uploading'} onFile={onFile} />

        {state.status === 'idle' && <EmptyState />}
        {state.status === 'uploading' && <LoadingState />}
        {state.status === 'error' && (
          <ErrorState
            message={state.message}
            canRetry={state.file !== null}
            onRetry={() => state.file && analyze(state.file)}
            onReset={reset}
          />
        )}
        {state.status === 'done' && <ResultView result={state.result} />}

        <HistoryPanel
          entries={history}
          onOpen={openEntry}
          onDelete={(id) => setHistory(removeFromHistory(id))}
          onClear={() => setHistory(clearHistory())}
        />
      </main>
    </div>
  );
}
