const focus =
  'focus-visible:ring-2 focus-visible:ring-accent-600 focus-visible:ring-offset-2 focus-visible:ring-offset-ink-50 focus-visible:outline-none';

const buttonBase = `inline-flex cursor-pointer items-center justify-center rounded-md px-4 py-2 text-sm font-semibold transition-colors ${focus} aria-disabled:cursor-not-allowed aria-disabled:opacity-60`;

export const focusRing = focus;
export const primaryButton = `${buttonBase} bg-accent-500 text-ink-950 hover:bg-accent-400 active:bg-accent-600`;
export const secondaryButton = `${buttonBase} border border-ink-500 bg-white text-ink-900 hover:border-ink-900 hover:bg-ink-100`;
export const card =
  'rounded-md border border-ink-200 border-t-2 border-t-ink-900 bg-white p-5 sm:p-6';
export const cardTitle =
  'mb-4 font-mono text-xs font-semibold tracking-widest text-ink-600 uppercase';
export const mutedText = 'text-sm text-ink-600';
