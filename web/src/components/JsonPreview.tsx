import { useState } from 'react';
import { downloadJson } from '../lib/download';
import type { AnalysisResult } from '../lib/schema';

export function JsonPreview({ result }: { result: AnalysisResult }) {
  const [status, setStatus] = useState('');
  const json = JSON.stringify(result, null, 2);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(json);
      setStatus('Skopiowano.');
    } catch {
      setStatus('Nie udało się skopiować.');
    }
  };

  return (
    <section className="card">
      <h2>JSON</h2>
      <div className="actions">
        <button type="button" className="button" onClick={() => downloadJson(result)}>
          Pobierz JSON
        </button>
        <button type="button" className="button button--secondary" onClick={copy}>
          Kopiuj JSON
        </button>
        <span role="status" className="muted">
          {status}
        </span>
      </div>
      <details>
        <summary>Podgląd JSON</summary>
        <pre>{json}</pre>
      </details>
    </section>
  );
}
