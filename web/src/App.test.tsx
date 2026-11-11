import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, test } from 'vitest';
import App from './App';
import { InjectionBadge } from './components/InjectionBadge';
import { ResultView } from './components/ResultView';
import { validResult } from './lib/fixtures';
import { I18nProvider } from './lib/i18n';

beforeEach(() => {
  localStorage.clear();
});

afterEach(cleanup);

function renderInApp(ui: React.ReactNode) {
  return render(<I18nProvider>{ui}</I18nProvider>);
}

test('renders Polish by default', () => {
  renderInApp(<App />);
  expect(screen.getByRole('heading', { name: 'PDF Insight' })).toBeTruthy();
  expect(screen.getByText('Wybierz plik')).toBeTruthy();
  expect(screen.getByText(/Nie wgrywaj dokumentów z danymi wrażliwymi/)).toBeTruthy();
  expect(screen.getByTestId('lang-pl').getAttribute('aria-pressed')).toBe('true');
  expect(screen.getByTestId('lang-en').getAttribute('aria-pressed')).toBe('false');
});

test('the toggle switches the whole UI to English', () => {
  renderInApp(<App />);
  fireEvent.click(screen.getByTestId('lang-en'));
  expect(screen.getByText('Choose file')).toBeTruthy();
  expect(screen.getByText(/Do not upload documents containing sensitive data/)).toBeTruthy();
  expect(screen.getByTestId('lang-en').getAttribute('aria-pressed')).toBe('true');
  expect(document.documentElement.lang).toBe('en');
});

test('the injection badge is shown in both languages', () => {
  localStorage.setItem('pdf-insight:lang', 'pl');
  const { unmount } = renderInApp(<InjectionBadge />);
  expect(screen.getByTestId('injection').textContent).toContain('Wykryto podejrzaną treść.');
  unmount();

  localStorage.setItem('pdf-insight:lang', 'en');
  renderInApp(<InjectionBadge />);
  expect(screen.getByTestId('injection').textContent).toContain('Suspicious content detected.');
});

test('the result view follows the language, including date and amount formats', () => {
  renderInApp(
    <>
      <App />
      <ResultView result={validResult} />
    </>,
  );
  expect(screen.getAllByText('Najważniejsze punkty').length).toBeGreaterThan(0);
  expect(screen.getAllByText(/12 marca 2026/).length).toBeGreaterThan(0);
  fireEvent.click(screen.getByTestId('lang-en'));
  expect(screen.getAllByText('Key points').length).toBeGreaterThan(0);
  expect(screen.getAllByText(/12 March 2026/).length).toBeGreaterThan(0);
});
