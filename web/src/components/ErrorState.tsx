import { primaryButton, secondaryButton } from './ui';

type Props = {
  message: string;
  canRetry: boolean;
  onRetry: () => void;
  onReset: () => void;
};

export function ErrorState({ message, canRetry, onRetry, onReset }: Props) {
  return (
    <div
      data-testid="error"
      className="rounded-xl border border-red-300 bg-red-50 p-5 text-red-900"
      role="alert"
    >
      <p className="font-medium">{message}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        {canRetry && (
          <button type="button" className={primaryButton} onClick={onRetry}>
            Spróbuj ponownie
          </button>
        )}
        <button type="button" className={secondaryButton} onClick={onReset}>
          Wybierz inny plik
        </button>
      </div>
    </div>
  );
}
