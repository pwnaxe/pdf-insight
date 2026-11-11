import { useRef, useState, type DragEvent, type KeyboardEvent } from 'react';
import { useI18n } from '../lib/i18n';
import { primaryButton } from './ui';

type Props = {
  disabled?: boolean;
  onFile: (file: File) => void;
};

export function Dropzone({ disabled = false, onFile }: Props) {
  const { t } = useI18n();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const open = () => inputRef.current?.click();

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      open();
    }
  };

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files[0];
    if (file && !disabled) onFile(file);
  };

  return (
    <div
      className={`flex flex-col items-center gap-3 rounded-2xl border-2 border-dashed px-4 py-12 text-center transition-colors ${
        dragging
          ? 'border-indigo-600 bg-indigo-50'
          : 'border-slate-300 bg-white hover:border-indigo-400 hover:bg-indigo-50/50'
      }`}
      role="group"
      aria-label={t.dropAria}
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
    >
      <p className="text-lg font-medium text-slate-900">{t.dropTitle}</p>
      <div
        className={primaryButton}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
        onClick={disabled ? undefined : open}
        onKeyDown={disabled ? undefined : onKeyDown}
      >
        {t.chooseFile}
      </div>
      <p className="text-sm text-slate-600">{t.dropHint}</p>
      <input
        ref={inputRef}
        className="sr-only"
        type="file"
        accept="application/pdf"
        tabIndex={-1}
        disabled={disabled}
        data-testid="file-input"
        onChange={(event) => {
          const file = event.target.files?.[0];
          event.target.value = '';
          if (file) onFile(file);
        }}
      />
    </div>
  );
}
