import { useEffect, useState } from 'react';
import { card } from './ui';

const UPLOAD_STEP_SECONDS = 2;

export function LoadingState() {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setSeconds((value) => value + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const step = seconds < UPLOAD_STEP_SECONDS ? 'Uploading file…' : 'Analysing document…';

  return (
    <div className={`${card} flex items-center gap-3`} role="status" aria-live="polite">
      <span
        className="size-5 shrink-0 rounded-full border-[3px] border-slate-200 border-t-indigo-600 motion-safe:animate-spin"
        aria-hidden="true"
      />
      <span>
        {step} <span className="text-sm text-slate-600">({seconds} s)</span>
      </span>
    </div>
  );
}
