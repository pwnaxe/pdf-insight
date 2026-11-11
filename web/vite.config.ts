import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv, type Plugin } from 'vite';
import { buildCsp } from './csp.ts';

// Build only: the dev server needs inline scripts for HMR.
function cspPlugin(apiUrl: string | undefined): Plugin {
  return {
    name: 'pdf-insight-csp',
    apply: 'build',
    transformIndexHtml() {
      return [
        {
          tag: 'meta',
          attrs: { 'http-equiv': 'Content-Security-Policy', content: buildCsp(apiUrl) },
          injectTo: 'head-prepend',
        },
        {
          tag: 'meta',
          attrs: { name: 'referrer', content: 'no-referrer' },
          injectTo: 'head-prepend',
        },
      ];
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');
  return {
    base: '/pdf-insight/',
    plugins: [react(), tailwindcss(), cspPlugin(process.env.VITE_API_URL ?? env.VITE_API_URL)],
    // tiny font subsets would otherwise be inlined as data: URIs, which font-src 'self' blocks
    build: { assetsInlineLimit: 0 },
    test: {
      environment: 'jsdom',
    },
  };
});
