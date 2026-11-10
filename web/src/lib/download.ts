import type { AnalysisResult } from './schema';

export function jsonFileName(fileName: string): string {
  const base = fileName.replace(/\.pdf$/i, '').trim();
  return `${base || 'dokument'}.insight.json`;
}

export function downloadJson(result: AnalysisResult): void {
  const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = jsonFileName(result.document.fileName);
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
