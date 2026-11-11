import { useEffect, useState } from 'react';
import { useI18n } from '../lib/i18n';
import { card } from './ui';

const UPLOAD_STEP_SECONDS = 2;

export function LoadingState() {
  const { t } = useI18n();
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setSeconds((value) => value + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const step = seconds < UPLOAD_STEP_SECONDS ? t.uploading : t.analysing;

  return (
    <div className={`${card} flex items-center gap-3`} role="status" aria-live="polite">
      <span
        className="size-5 shrink-0 rounded-full border-[3px] border-slate-200 border-t-indigo-600 motion-safe:animate-spin"
        aria-hidden="true"
      />
      <span>
        {step} <span className="text-sm text-slate-600">({t.seconds(seconds)})</span>
      </span>
    </div>
  );
}
