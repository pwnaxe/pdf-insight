type Props = {
  message: string;
  canRetry: boolean;
  onRetry: () => void;
  onReset: () => void;
};

export function ErrorState({ message, canRetry, onRetry, onReset }: Props) {
  return (
    <div className="error" role="alert">
      <p>{message}</p>
      <div className="actions">
        {canRetry && (
          <button type="button" className="button" onClick={onRetry}>
            Spróbuj ponownie
          </button>
        )}
        <button type="button" className="button button--secondary" onClick={onReset}>
          Wybierz inny plik
        </button>
      </div>
    </div>
  );
}
