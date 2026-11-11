import type { Messages } from './i18n';

export const MAX_FILE_BYTES = 10 * 1024 * 1024;

const PDF_MAGIC = '%PDF-';

export async function validateFile(file: File, t: Messages): Promise<string | null> {
  const looksLikePdf = file.type === 'application/pdf' || /\.pdf$/i.test(file.name);
  if (!looksLikePdf) {
    return t.validation.notPdf;
  }
  if (file.size === 0) {
    return t.validation.empty;
  }
  if (file.size > MAX_FILE_BYTES) {
    return t.validation.tooLarge;
  }
  const head = await file.slice(0, PDF_MAGIC.length).text();
  if (head !== PDF_MAGIC) {
    return t.validation.badSignature;
  }
  return null;
}
