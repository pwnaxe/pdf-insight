import { z } from 'zod';

const isoDate = z.string().refine((value) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().startsWith(value);
}, 'Invalid date');

const DocumentTypeSchema = z.enum(['faktura', 'umowa', 'oferta', 'raport', 'inne']);

export const AnalysisResultSchema = z.object({
  document: z.object({
    fileName: z.string(),
    pages: z.number().int().min(1),
    language: z.string().regex(/^[a-z]{2}$/),
    type: DocumentTypeSchema,
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
  dates: z.array(z.object({ date: isoDate, context: z.string() })),
  keywords: z.array(z.string()),
  suspectedInjection: z.boolean(),
  warnings: z.array(z.string()),
});

export type AnalysisResult = z.infer<typeof AnalysisResultSchema>;
