import type { AnalysisResult } from './schema';

export const validResult: AnalysisResult = {
  document: {
    fileName: 'Test_PDF_Insight_umowa_14-2026.pdf',
    pages: 12,
    language: 'pl',
    type: 'umowa',
    title: 'Umowa nr 14/2026 o świadczenie usług',
    date: '2026-03-12',
  },
  summary:
    'Umowa została zawarta między Nordwave Logistics sp. z o.o. a Kwadrat Software S.A. Dotyczy wdrożenia systemu. Wynagrodzenie wynosi 184 500,00 zł netto.',
  keyPoints: [
    'Wynagrodzenie 184 500,00 PLN netto',
    'Brutto 226 935,00 PLN',
    'Zawarta 12 marca 2026',
  ],
  entities: {
    organizations: ['Nordwave Logistics sp. z o.o.', 'Kwadrat Software S.A.'],
    people: [],
  },
  amounts: [
    { value: 184500, currency: 'PLN', context: 'wynagrodzenie netto' },
    { value: 226935, currency: 'PLN', context: 'wynagrodzenie brutto' },
    { value: 8600, currency: 'EUR', context: 'licencja' },
    { value: 890, currency: 'USD', context: 'opłata miesięczna' },
    { value: 12300, currency: 'PLN', context: 'kara umowna' },
  ],
  dates: [{ date: '2026-03-12', context: 'data zawarcia umowy' }],
  keywords: ['umowa', 'wdrożenie', 'licencja'],
  suspectedInjection: true,
  warnings: ['Strony bez warstwy tekstowej (pominięte): 11.'],
};
