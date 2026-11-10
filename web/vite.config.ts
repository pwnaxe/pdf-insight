import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  base: '/pdf-insight/',
  plugins: [react()],
  test: {
    environment: 'jsdom',
  },
});
