import { formatAmountValue, formatDate, formatPreciseDate } from '../lib/format';
import type { AnalysisResult } from '../lib/schema';
import { useI18n } from '../lib/i18n';
import { InjectionBadge } from './InjectionBadge';
import { JsonPreview } from './JsonPreview';
import { card, cardTitle, mutedText } from './ui';

const subTitle = 'mb-2 mt-5 text-sm font-semibold text-ink-700 first:mt-0';
const list = 'list-disc space-y-1.5 pl-5 marker:text-accent-600';
const badge = 'inline-flex items-center rounded px-2 py-0.5 font-mono text-xs font-semibold';
const th = 'py-2 font-mono text-xs font-semibold tracking-wider text-ink-600 uppercase';

function NameList({ title, names }: { title: string; names: string[] }) {
  const { t } = useI18n();
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
        <p className={mutedText}>{t.none}</p>
      )}
    </>
  );
}

export function ResultView({ result }: { result: AnalysisResult }) {
  const { lang, t } = useI18n();
  const { document: doc, entities } = result;
  const meta = [
    { label: t.language, value: doc.language },
    { label: t.date, value: doc.date ? formatDate(doc.date, lang) : t.noDate, mono: true },
    { label: t.pages, value: String(doc.pages), mono: true },
    { label: t.file, value: doc.fileName },
  ];

  return (
    <div className="flex flex-col gap-6">
      {result.suspectedInjection && <InjectionBadge />}

      <section className={card} aria-labelledby="summary-title">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-mono text-xs font-semibold tracking-widest text-ink-600 uppercase">
            {t.analysisResult}
          </p>
          <span className={`${badge} bg-ink-900 text-white`}>{doc.type}</span>
          {doc.subtype && (
            <span className={`${badge} border border-accent-700 text-accent-800`}>
              {doc.subtype}
            </span>
          )}
        </div>
        <h2
          id="summary-title"
          className="mt-3 text-2xl font-bold tracking-tight [overflow-wrap:anywhere] text-ink-950 sm:text-3xl"
        >
          {doc.title ?? doc.fileName}
        </h2>
        <h3 className={`${subTitle} mt-5`}>{t.summary}</h3>
        <p data-testid="summary" className="max-w-prose leading-relaxed text-ink-800">
          {result.summary}
        </p>
        <dl className="mt-6 grid grid-cols-2 gap-x-4 gap-y-3 border-t border-ink-200 pt-4 sm:grid-cols-4">
          {meta.map(({ label, value, mono }) => (
            <div key={label} className="min-w-0">
              <dt className="text-xs font-medium text-ink-600">{label}</dt>
              <dd
                className={`text-sm font-medium [overflow-wrap:anywhere] ${mono ? 'font-mono tabular-nums' : ''}`}
              >
                {value}
              </dd>
            </div>
          ))}
        </dl>
      </section>

      {result.warnings.length > 0 && (
        <section
          data-testid="warnings"
          className="rounded-md border border-l-4 border-ink-200 border-l-accent-600 bg-accent-50 p-5 text-accent-900"
          aria-label={t.warnings}
        >
          <h2 className="mb-2 font-mono text-xs font-semibold tracking-widest uppercase">
            {t.warnings}
          </h2>
          <ul className="list-disc space-y-1 pl-5">
            {result.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </section>
      )}

      <section className={card}>
        <h2 className={cardTitle}>{t.keyPoints}</h2>
        <ul className={list}>
          {result.keyPoints.map((point) => (
            <li key={point}>{point}</li>
          ))}
        </ul>
      </section>

      <section className={card}>
        <h2 className={cardTitle}>{t.entities}</h2>
        <NameList title={t.organizations} names={entities.organizations} />
        <NameList title={t.people} names={entities.people} />
      </section>

      <section className={card}>
        <h2 className={cardTitle}>{t.amounts}</h2>
        {result.amounts.length > 0 ? (
          <table className="w-full text-left text-sm">
            <thead className="sr-only sm:not-sr-only sm:table-header-group">
              <tr className="border-b border-ink-200">
                <th scope="col" className={`${th} pr-4 text-right`}>
                  {t.amount}
                </th>
                <th scope="col" className={`${th} pr-6 pl-3`}>
                  {t.currency}
                </th>
                <th scope="col" className={th}>
                  {t.context}
                </th>
              </tr>
            </thead>
            <tbody className="max-sm:block">
              {result.amounts.map((amount, index) => (
                <tr
                  key={`${amount.value}-${amount.currency}-${index}`}
                  className="border-b border-ink-100 last:border-0 max-sm:grid max-sm:grid-cols-[1fr_auto] max-sm:gap-x-3 max-sm:py-3"
                >
                  <td className="py-2.5 pr-4 text-right align-top font-mono font-semibold whitespace-nowrap tabular-nums max-sm:py-0 max-sm:text-left max-sm:text-base">
                    {formatAmountValue(amount.value, lang)}
                  </td>
                  <td className="py-2.5 pr-6 pl-3 align-top font-mono text-ink-700 max-sm:p-0 max-sm:text-base">
                    {amount.currency}
                  </td>
                  <td className="py-2.5 align-top text-ink-700 max-sm:col-span-2 max-sm:py-0 max-sm:pt-1">
                    {amount.context}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className={mutedText}>{t.none}</p>
        )}
      </section>

      <section className={card}>
        <h2 className={cardTitle}>{t.dates}</h2>
        {result.dates.length > 0 ? (
          <table className="w-full text-left text-sm">
            <thead className="sr-only sm:not-sr-only sm:table-header-group">
              <tr className="border-b border-ink-200">
                <th scope="col" className={`${th} pr-6`}>
                  {t.date}
                </th>
                <th scope="col" className={th}>
                  {t.context}
                </th>
              </tr>
            </thead>
            <tbody className="max-sm:block">
              {result.dates.map((item, index) => (
                <tr
                  key={`${item.date}-${index}`}
                  className="border-b border-ink-100 last:border-0 max-sm:block max-sm:py-3"
                >
                  <td className="py-2.5 pr-6 align-top font-mono font-semibold whitespace-nowrap tabular-nums max-sm:block max-sm:py-0">
                    {formatPreciseDate(item.date, item.precision, lang)}
                  </td>
                  <td className="py-2.5 align-top text-ink-700 max-sm:block max-sm:py-0 max-sm:pt-1">
                    {item.context}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className={mutedText}>{t.none}</p>
        )}
      </section>

      <section className={card}>
        <h2 className={cardTitle}>{t.keywords}</h2>
        <ul className="flex flex-wrap gap-2">
          {result.keywords.map((keyword) => (
            <li
              key={keyword}
              className="rounded-full border border-ink-300 bg-ink-100 px-3 py-1 text-sm font-medium text-ink-800"
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
