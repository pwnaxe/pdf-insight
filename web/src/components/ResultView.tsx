import { formatAmount, formatDate } from '../lib/format';
import type { AnalysisResult } from '../lib/schema';
import { InjectionBadge } from './InjectionBadge';
import { JsonPreview } from './JsonPreview';

export function ResultView({ result }: { result: AnalysisResult }) {
  const { document: doc, entities } = result;

  return (
    <div className="result">
      <header className="card">
        <h2>{doc.title ?? doc.fileName}</h2>
        <dl className="meta">
          <div>
            <dt>Typ</dt>
            <dd>{doc.type}</dd>
          </div>
          <div>
            <dt>Język</dt>
            <dd>{doc.language}</dd>
          </div>
          <div>
            <dt>Data</dt>
            <dd>{doc.date ? formatDate(doc.date) : 'brak'}</dd>
          </div>
          <div>
            <dt>Strony</dt>
            <dd>{doc.pages}</dd>
          </div>
          <div>
            <dt>Plik</dt>
            <dd className="break">{doc.fileName}</dd>
          </div>
        </dl>
      </header>

      {result.suspectedInjection && <InjectionBadge />}

      {result.warnings.length > 0 && (
        <section className="card warnings" aria-label="Ostrzeżenia">
          <h2>Ostrzeżenia</h2>
          <ul>
            {result.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="card">
        <h2>Streszczenie</h2>
        <p data-testid="summary">{result.summary}</p>
      </section>

      <section className="card">
        <h2>Najważniejsze punkty</h2>
        <ul>
          {result.keyPoints.map((point) => (
            <li key={point}>{point}</li>
          ))}
        </ul>
      </section>

      <section className="card">
        <h2>Podmioty</h2>
        <h3>Organizacje</h3>
        {entities.organizations.length > 0 ? (
          <ul>
            {entities.organizations.map((name) => (
              <li key={name}>{name}</li>
            ))}
          </ul>
        ) : (
          <p className="muted">Brak</p>
        )}
        <h3>Osoby</h3>
        {entities.people.length > 0 ? (
          <ul>
            {entities.people.map((name) => (
              <li key={name}>{name}</li>
            ))}
          </ul>
        ) : (
          <p className="muted">Brak</p>
        )}
      </section>

      <section className="card">
        <h2>Kwoty</h2>
        {result.amounts.length > 0 ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Kwota</th>
                  <th scope="col">Kontekst</th>
                </tr>
              </thead>
              <tbody>
                {result.amounts.map((amount, index) => (
                  <tr key={`${amount.value}-${amount.currency}-${index}`}>
                    <td className="nowrap">{formatAmount(amount.value, amount.currency)}</td>
                    <td>{amount.context}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="muted">Brak</p>
        )}
      </section>

      <section className="card">
        <h2>Daty</h2>
        {result.dates.length > 0 ? (
          <ul>
            {result.dates.map((item, index) => (
              <li key={`${item.date}-${index}`}>
                <strong>{formatDate(item.date)}</strong> - {item.context}
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">Brak</p>
        )}
      </section>

      <section className="card">
        <h2>Słowa kluczowe</h2>
        <ul className="chips">
          {result.keywords.map((keyword) => (
            <li key={keyword}>{keyword}</li>
          ))}
        </ul>
      </section>

      <JsonPreview result={result} />
    </div>
  );
}
