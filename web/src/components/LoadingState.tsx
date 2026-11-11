import { useEffect, useState } from 'react';
import { useI18n } from '../lib/i18n';
import { card } from './ui';

const UPLOAD_STEP_SECONDS = 2;
const bar = 'rounded bg-ink-200 motion-safe:animate-pulse';

export function LoadingState() {
  const { t } = useI18n();
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setSeconds((value) => value + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const step = seconds < UPLOAD_STEP_SECONDS ? t.uploading : t.analysing;

  return (
    <div className={card}>
      <p role="status" aria-live="polite" className="font-medium">
        {step} <span className="font-mono text-sm text-ink-600">({t.seconds(seconds)})</span>
      </p>
      <div className="mt-5 flex flex-col gap-3" aria-hidden="true">
        <div className={`${bar} h-6 w-2/3`} />
        <div className={`${bar} h-4 w-full`} />
        <div className={`${bar} h-4 w-11/12`} />
        <div className={`${bar} h-4 w-4/5`} />
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <div className={`${bar} h-16`} />
          <div className={`${bar} h-16`} />
        </div>
      </div>
    </div>
  );
}
