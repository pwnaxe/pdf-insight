import { useEffect, useState } from 'react';

const UPLOAD_STEP_SECONDS = 2;

export function LoadingState() {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setSeconds((value) => value + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const step = seconds < UPLOAD_STEP_SECONDS ? 'Wysyłam plik…' : 'Analizuję dokument…';

  return (
    <div className="loading" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <span>
        {step} <span className="muted">({seconds} s)</span>
      </span>
    </div>
  );
}
