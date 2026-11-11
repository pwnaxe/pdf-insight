export const MAX_FILE_BYTES = 10 * 1024 * 1024;

const PDF_MAGIC = '%PDF-';

export async function validateFile(file: File): Promise<string | null> {
  const looksLikePdf = file.type === 'application/pdf' || /\.pdf$/i.test(file.name);
  if (!looksLikePdf) {
    return 'Choose a PDF file.';
  }
  if (file.size === 0) {
    return 'This file is empty.';
  }
  if (file.size > MAX_FILE_BYTES) {
    return 'The file is too large. The maximum size is 10 MB.';
  }
  const head = await file.slice(0, PDF_MAGIC.length).text();
  if (head !== PDF_MAGIC) {
    return 'This file does not look like a valid PDF document.';
  }
  return null;
}
