import { LANGS, useI18n, type Lang } from '../lib/i18n';
import { focusRing } from './ui';

const base = `cursor-pointer px-3 py-1.5 font-mono text-xs font-semibold transition-colors focus-visible:z-10 ${focusRing}`;

export function LanguageToggle() {
  const { lang, setLang, t } = useI18n();

  return (
    <div
      role="group"
      aria-label={t.languageLabel}
      className="inline-flex overflow-hidden rounded-md border border-ink-500 bg-white"
    >
      {LANGS.map((code: Lang) => (
        <button
          key={code}
          type="button"
          lang={code}
          aria-pressed={lang === code}
          data-testid={`lang-${code}`}
          className={`${base} ${
            lang === code ? 'bg-ink-900 text-white' : 'text-ink-700 hover:bg-ink-100'
          }`}
          onClick={() => setLang(code)}
        >
          {code.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
