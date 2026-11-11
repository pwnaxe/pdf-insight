import { useI18n } from '../lib/i18n';
import { primaryButton, secondaryButton } from './ui';

type Props = {
  message: string;
  canRetry: boolean;
  onRetry: () => void;
  onReset: () => void;
};

export function ErrorState({ message, canRetry, onRetry, onReset }: Props) {
  const { t } = useI18n();
  return (
    <div
      data-testid="error"
      className="rounded-md border border-red-700 bg-red-50 p-5 text-red-950"
      role="alert"
    >
      <p className="font-medium">{message}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        {canRetry && (
          <button type="button" className={primaryButton} onClick={onRetry}>
            {t.tryAgain}
          </button>
        )}
        <button type="button" className={secondaryButton} onClick={onReset}>
          {t.chooseAnother}
        </button>
      </div>
    </div>
  );
}
