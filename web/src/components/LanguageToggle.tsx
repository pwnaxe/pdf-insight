import { LANGS, useI18n, type Lang } from '../lib/i18n';

const base =
  'px-3 py-1 text-sm font-medium focus-visible:z-10 focus-visible:ring-2 focus-visible:ring-indigo-600 focus-visible:ring-offset-2 focus-visible:outline-none';

export function LanguageToggle() {
  const { lang, setLang, t } = useI18n();

  return (
    <div
      role="group"
      aria-label={t.languageLabel}
      className="inline-flex overflow-hidden rounded-lg border border-slate-300 bg-white"
    >
      {LANGS.map((code: Lang) => (
        <button
          key={code}
          type="button"
          lang={code}
          aria-pressed={lang === code}
          data-testid={`lang-${code}`}
          className={`${base} ${
            lang === code ? 'bg-indigo-700 text-white' : 'text-slate-700 hover:bg-slate-100'
          }`}
          onClick={() => setLang(code)}
        >
          {code.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
