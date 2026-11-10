import { useRef, useState, type DragEvent, type KeyboardEvent } from 'react';

type Props = {
  disabled?: boolean;
  onFile: (file: File) => void;
};

export function Dropzone({ disabled = false, onFile }: Props) {
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
      className={`dropzone${dragging ? ' dropzone--over' : ''}`}
      role="group"
      aria-label="Wgraj plik PDF"
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
    >
      <p>Przeciągnij plik PDF tutaj lub</p>
      <div
        className="button"
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
        onClick={disabled ? undefined : open}
        onKeyDown={disabled ? undefined : onKeyDown}
      >
        Wybierz plik
      </div>
      <p className="hint">PDF z warstwą tekstową, do 10 MB.</p>
      <input
        ref={inputRef}
        className="visually-hidden"
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
