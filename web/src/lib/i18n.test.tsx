import { act, cleanup, render, renderHook } from '@testing-library/react';
import type { ReactNode } from 'react';
import { afterEach, beforeEach, expect, test } from 'vitest';
import {
  DEFAULT_LANG,
  I18nProvider,
  LANG_STORAGE_KEY,
  dictionary,
  localeFor,
  parseLang,
  useI18n,
} from './i18n';

const wrapper = ({ children }: { children: ReactNode }) => <I18nProvider>{children}</I18nProvider>;

afterEach(cleanup);

beforeEach(() => {
  localStorage.clear();
  document.documentElement.lang = '';
});

test('defaults to Polish and sets the html lang', () => {
  const { result } = renderHook(() => useI18n(), { wrapper });
  expect(result.current.lang).toBe('pl');
  expect(result.current.t.chooseFile).toBe('Wybierz plik');
  expect(document.documentElement.lang).toBe('pl');
});

test('persists the choice and keeps html lang in sync', () => {
  const { result } = renderHook(() => useI18n(), { wrapper });
  act(() => result.current.setLang('en'));
  expect(result.current.t.chooseFile).toBe('Choose file');
  expect(localStorage.getItem(LANG_STORAGE_KEY)).toBe('en');
  expect(document.documentElement.lang).toBe('en');
});

test('restores the stored language', () => {
  localStorage.setItem(LANG_STORAGE_KEY, 'en');
  const { result } = renderHook(() => useI18n(), { wrapper });
  expect(result.current.lang).toBe('en');
  expect(document.documentElement.lang).toBe('en');
});

test('ignores an invalid stored value', () => {
  localStorage.setItem(LANG_STORAGE_KEY, 'de');
  const { result } = renderHook(() => useI18n(), { wrapper });
  expect(result.current.lang).toBe(DEFAULT_LANG);
});

test('maps languages to locales', () => {
  expect(localeFor('pl')).toBe('pl-PL');
  expect(localeFor('en')).toBe('en-GB');
  expect(parseLang('en')).toBe('en');
  expect(parseLang(undefined)).toBe('pl');
});

test('both dictionaries cover the same error codes', () => {
  expect(Object.keys(dictionary.pl.errors).sort()).toEqual(
    Object.keys(dictionary.en.errors).sort(),
  );
});

test('throws outside the provider', () => {
  expect(() => render(<Bare />)).toThrow(/I18nProvider/);
});

function Bare() {
  useI18n();
  return null;
}
