import { z } from 'zod';

const isoDate = z.string().refine((value) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().startsWith(value);
}, 'Invalid date');

export type DatePrecision = 'year' | 'month' | 'day';

export function datePrecision(value: string): DatePrecision | null {
  const match = /^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$/.exec(value);
  if (!match) return null;
  const [, year, month, day] = match;
  if (day && !month) return null;
  const m = Number(month ?? 1);
  const d = Number(day ?? 1);
  const lastDay = new Date(Date.UTC(Number(year), m, 0)).getUTCDate();
  if (m < 1 || m > 12 || d < 1 || d > lastDay) return null;
  return day ? 'day' : month ? 'month' : 'year';
}

// entries saved before the precision field existed have none: derive it from the date
const datedItem = z
  .object({
    date: z.string(),
    precision: z.enum(['year', 'month', 'day']).optional(),
    context: z.string(),
  })
  .transform((item, ctx) => {
    const precision = datePrecision(item.date);
    if (precision === null || (item.precision && item.precision !== precision)) {
      ctx.addIssue({ code: 'custom', message: 'Invalid date' });
      return z.NEVER;
    }
    return { date: item.date, precision, context: item.context };
  });

const DocumentTypeSchema = z.enum(['faktura', 'umowa', 'oferta', 'raport', 'inne']);

export const AnalysisResultSchema = z.object({
  document: z.object({
    fileName: z.string(),
    pages: z.number().int().min(1),
    language: z.string().regex(/^[a-z]{2}$/),
    type: DocumentTypeSchema,
    subtype: z
      .string()
      .min(1)
      .max(30)
      .refine((value) => value === value.toLowerCase(), 'Must be lowercase')
      .nullish(),
    title: z.string().nullable(),
    date: isoDate.nullable(),
  }),
  summary: z.string().min(1),
  keyPoints: z.array(z.string()).min(3).max(7),
  entities: z.object({
    organizations: z.array(z.string()),
    people: z.array(z.string()),
  }),
  amounts: z.array(
    z.object({
      value: z.number(),
      currency: z.string().regex(/^[A-Z]{3}$/),
      context: z.string(),
    }),
  ),
  dates: z.array(datedItem),
  keywords: z.array(z.string()),
  suspectedInjection: z.boolean(),
  warnings: z.array(z.string()),
});

export type AnalysisResult = z.infer<typeof AnalysisResultSchema>;
