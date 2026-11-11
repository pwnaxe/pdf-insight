import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
import App from './App';

test('renders the heading, upload control and notice', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: 'PDF Insight' })).toBeTruthy();
  expect(screen.getByText('Choose file')).toBeTruthy();
  expect(screen.getByText(/Do not upload documents containing sensitive data/)).toBeTruthy();
});
