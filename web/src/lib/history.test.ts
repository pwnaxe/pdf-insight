import { beforeEach, describe, expect, test } from 'vitest';
import {
  addToHistory,
  clearHistory,
  HISTORY_KEY,
  HISTORY_LIMIT,
  loadHistory,
  removeFromHistory,
} from './history';
import { validResult } from './fixtures';

class FakeStorage implements Storage {
  private data = new Map<string, string>();
  throwOnSet = false;
  get length() {
    return this.data.size;
  }
  clear() {
    this.data.clear();
  }
  getItem(key: string) {
    return this.data.get(key) ?? null;
  }
  key(index: number) {
    return [...this.data.keys()][index] ?? null;
  }
  removeItem(key: string) {
    this.data.delete(key);
  }
  setItem(key: string, value: string) {
    if (this.throwOnSet) throw new DOMException('full', 'QuotaExceededError');
    this.data.set(key, value);
  }
}

let storage: FakeStorage;

beforeEach(() => {
  storage = new FakeStorage();
});

describe('history', () => {
  test('starts empty', () => {
    expect(loadHistory(storage)).toEqual([]);
  });

  test('stores newest first and survives a reload', () => {
    addToHistory(validResult, storage, new Date('2026-03-12T10:00:00Z'));
    const second = structuredClone(validResult);
    second.document.fileName = 'druga.pdf';
    addToHistory(second, storage, new Date('2026-03-12T11:00:00Z'));
    const loaded = loadHistory(storage);
    expect(loaded.map((e) => e.result.document.fileName)).toEqual([
      'druga.pdf',
      validResult.document.fileName,
    ]);
  });

  test('keeps only the last 10 entries', () => {
    for (let i = 0; i < HISTORY_LIMIT + 3; i++) {
      addToHistory(validResult, storage, new Date(2026, 0, 1, 0, i));
    }
    expect(loadHistory(storage)).toHaveLength(HISTORY_LIMIT);
  });

  test('drops invalid entries on load', () => {
    addToHistory(validResult, storage);
    const stored = JSON.parse(storage.getItem(HISTORY_KEY) ?? '[]') as unknown[];
    stored.push({ id: 'x', savedAt: 'now', result: { broken: true } });
    storage.setItem(HISTORY_KEY, JSON.stringify(stored));
    expect(loadHistory(storage)).toHaveLength(1);
  });

  test('ignores corrupted JSON', () => {
    storage.setItem(HISTORY_KEY, '{not json');
    expect(loadHistory(storage)).toEqual([]);
  });

  test('ignores quota errors', () => {
    storage.throwOnSet = true;
    expect(() => addToHistory(validResult, storage)).not.toThrow();
  });

  test('removes one entry and clears all', () => {
    addToHistory(validResult, storage);
    const entries = addToHistory(validResult, storage);
    const target = entries.at(0)?.id ?? '';
    expect(removeFromHistory(target, storage)).toHaveLength(1);
    expect(clearHistory(storage)).toEqual([]);
    expect(loadHistory(storage)).toEqual([]);
  });
});
