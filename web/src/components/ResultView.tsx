import { formatAmount, formatDate } from '../lib/format';
import type { AnalysisResult } from '../lib/schema';
import { InjectionBadge } from './InjectionBadge';
import { JsonPreview } from './JsonPreview';
import { card, cardTitle, mutedText } from './ui';

const subTitle = 'mb-1 mt-4 text-sm font-semibold text-slate-700 first:mt-0';
const list = 'list-disc space-y-1 pl-5 marker:text-slate-400';

function NameList({ title, names }: { title: string; names: string[] }) {
  return (
    <>
      <h3 className={subTitle}>{title}</h3>
      {names.length > 0 ? (
        <ul className={list}>
          {names.map((name) => (
            <li key={name}>{name}</li>
          ))}
        </ul>
      ) : (
        <p className={mutedText}>Brak</p>
      )}
    </>
  );
}

export function ResultView({ result }: { result: AnalysisResult }) {
  const { document: doc, entities } = result;
  const meta = [
    { label: 'Typ', value: doc.type },
    { label: 'Język', value: doc.language },
    { label: 'Data', value: doc.date ? formatDate(doc.date) : 'brak' },
    { label: 'Strony', value: String(doc.pages) },
    { label: 'Plik', value: doc.fileName },
  ];

  return (
    <div className="flex flex-col gap-6">
      {result.suspectedInjection && <InjectionBadge />}

      <section className={card} aria-labelledby="summary-title">
        <p className="text-xs font-semibold tracking-wide text-indigo-700 uppercase">
          Wynik analizy
        </p>
        <h2 id="summary-title" className="mt-1 text-2xl font-semibold [overflow-wrap:anywhere]">
          {doc.title ?? doc.fileName}
        </h2>
        <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 border-b border-slate-200 pb-5 sm:grid-cols-5">
          {meta.map(({ label, value }) => (
            <div key={label} className="min-w-0">
              <dt className="text-xs font-medium text-slate-600">{label}</dt>
              <dd className="text-sm font-medium [overflow-wrap:anywhere]">{value}</dd>
            </div>
          ))}
        </dl>
        <h3 className={`${subTitle} mt-5`}>Streszczenie</h3>
        <p data-testid="summary" className="leading-relaxed text-slate-800">
          {result.summary}
        </p>
      </section>

      {result.warnings.length > 0 && (
        <section
          className="warnings rounded-xl border border-amber-300 bg-amber-50 p-5 text-amber-950"
          aria-label="Ostrzeżenia"
        >
          <h2 className="mb-2 text-lg font-semibold">Ostrzeżenia</h2>
          <ul className="list-disc space-y-1 pl-5">
            {result.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </section>
      )}

      <section className={card}>
        <h2 className={cardTitle}>Najważniejsze punkty</h2>
        <ul className={list}>
          {result.keyPoints.map((point) => (
            <li key={point}>{point}</li>
          ))}
        </ul>
      </section>

      <section className={card}>
        <h2 className={cardTitle}>Podmioty</h2>
        <NameList title="Organizacje" names={entities.organizations} />
        <NameList title="Osoby" names={entities.people} />
      </section>

      <section className={card}>
        <h2 className={cardTitle}>Kwoty</h2>
        {result.amounts.length > 0 ? (
          <table className="w-full text-left text-sm">
            <thead className="sr-only sm:not-sr-only sm:table-header-group">
              <tr className="border-b border-slate-200 text-slate-600">
                <th scope="col" className="py-2 pr-4 font-semibold">
                  Kwota
                </th>
                <th scope="col" className="py-2 font-semibold">
                  Kontekst
                </th>
              </tr>
            </thead>
            <tbody className="max-sm:block">
              {result.amounts.map((amount, index) => (
                <tr
                  key={`${amount.value}-${amount.currency}-${index}`}
                  className="border-b border-slate-100 last:border-0 max-sm:block max-sm:py-3"
                >
                  <td className="py-2 pr-4 align-top font-semibold whitespace-nowrap max-sm:block max-sm:py-0 sm:py-2.5">
                    {formatAmount(amount.value, amount.currency)}
                  </td>
                  <td className="py-2 align-top text-slate-700 max-sm:block max-sm:py-0 sm:py-2.5">
                    {amount.context}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className={mutedText}>Brak</p>
        )}
      </section>

      <section className={card}>
        <h2 className={cardTitle}>Daty</h2>
        {result.dates.length > 0 ? (
          <ul className="divide-y divide-slate-100">
            {result.dates.map((item, index) => (
              <li key={`${item.date}-${index}`} className="py-2 first:pt-0 last:pb-0">
                <strong>{formatDate(item.date)}</strong>
                <span className="text-slate-700"> - {item.context}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className={mutedText}>Brak</p>
        )}
      </section>

      <section className={card}>
        <h2 className={cardTitle}>Słowa kluczowe</h2>
        <ul className="flex flex-wrap gap-2">
          {result.keywords.map((keyword) => (
            <li
              key={keyword}
              className="rounded-full bg-indigo-50 px-3 py-1 text-sm font-medium text-indigo-900 ring-1 ring-indigo-200 ring-inset"
            >
              {keyword}
            </li>
          ))}
        </ul>
      </section>

      <JsonPreview result={result} />
    </div>
  );
}
