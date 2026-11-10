export const MAX_FILE_BYTES = 10 * 1024 * 1024;

const PDF_MAGIC = '%PDF-';

export async function validateFile(file: File): Promise<string | null> {
  const looksLikePdf = file.type === 'application/pdf' || /\.pdf$/i.test(file.name);
  if (!looksLikePdf) {
    return 'Wybierz plik w formacie PDF.';
  }
  if (file.size === 0) {
    return 'Ten plik jest pusty.';
  }
  if (file.size > MAX_FILE_BYTES) {
    return 'Plik jest za duży. Maksymalny rozmiar to 10 MB.';
  }
  const head = await file.slice(0, PDF_MAGIC.length).text();
  if (head !== PDF_MAGIC) {
    return 'Ten plik nie wygląda na prawidłowy dokument PDF.';
  }
  return null;
}
