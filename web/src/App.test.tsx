import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
import App from './App';

test('renders the heading, upload control and notice', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: 'PDF Insight' })).toBeTruthy();
  expect(screen.getByText('Wybierz plik')).toBeTruthy();
  expect(screen.getByText(/Nie wgrywaj dokumentów z danymi wrażliwymi/)).toBeTruthy();
});
