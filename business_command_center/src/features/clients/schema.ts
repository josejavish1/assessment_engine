import { z } from 'zod';

export const clientSchema = z.object({
  name: z.string().min(3, 'El nombre corporativo debe tener al menos 3 caracteres'),
  slug: z
    .string()
    .min(3, 'El slug debe tener al menos 3 caracteres')
    .regex(/^[a-z0-9_-]+$/, 'Slug must contain only lowercase alphanumeric characters, hyphens, or underscores'),
  sector: z.enum([
    'Energy & Utilities',
    'Banca & Finanzas',
    'Healthcare & Pharma',
    'Industria & Consumo',
    'Public Sector',
    'Telco & Medium',
  ]),
  country: z.string().min(2, 'Must specify country or jurisdiction'),
  currency: z.string().min(1, 'Debe especificar la divisa operativa'),
  standard: z.string().min(2, 'Debe especificar el marco regulatorio principal'),
  description: z.string().optional(),
});

export type ClientFormValues = z.infer<typeof clientSchema>;
