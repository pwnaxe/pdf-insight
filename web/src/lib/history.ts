import { z } from 'zod';
import { AnalysisResultSchema, type AnalysisResult } from './schema';

export const HISTORY_KEY = 'pdf-insight:history:v1';
export const HISTORY_LIMIT = 10;

const EntrySchema = z.object({
  id: z.string(),
  savedAt: z.string(),
  result: AnalysisResultSchema,
});

export type HistoryEntry = z.infer<typeof EntrySchema>;

export function loadHistory(storage: Storage = localStorage): HistoryEntry[] {
  let raw: string | null;
  try {
    raw = storage.getItem(HISTORY_KEY);
  } catch {
    return [];
  }
  if (!raw) return [];
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return [];
  }
  if (!Array.isArray(parsed)) return [];
  const entries: HistoryEntry[] = [];
  for (const item of parsed) {
    const result = EntrySchema.safeParse(item);
    if (result.success) entries.push(result.data);
  }
  return entries.slice(0, HISTORY_LIMIT);
}

function save(entries: HistoryEntry[], storage: Storage): void {
  try {
    storage.setItem(HISTORY_KEY, JSON.stringify(entries));
  } catch {
    // Quota exceeded or storage disabled: history is best effort.
  }
}

export function addToHistory(
  result: AnalysisResult,
  storage: Storage = localStorage,
  now: Date = new Date(),
): HistoryEntry[] {
  const entry: HistoryEntry = {
    id: `${now.getTime()}-${Math.random().toString(36).slice(2, 8)}`,
    savedAt: now.toISOString(),
    result,
  };
  const next = [entry, ...loadHistory(storage)].slice(0, HISTORY_LIMIT);
  save(next, storage);
  return next;
}

export function removeFromHistory(id: string, storage: Storage = localStorage): HistoryEntry[] {
  const next = loadHistory(storage).filter((entry) => entry.id !== id);
  save(next, storage);
  return next;
}

export function clearHistory(storage: Storage = localStorage): HistoryEntry[] {
  try {
    storage.removeItem(HISTORY_KEY);
  } catch {
    // storage disabled
  }
  return [];
}
