import { z } from 'zod';

export const clientSchema = z.object({
  name: z.string().min(2, 'El nombre corporativo debe tener al menos 2 caracteres'),
  domain: z.string().min(3, 'El dominio corporativo es obligatorio').optional(),
  slug: z
    .string()
    .min(2, 'El slug debe tener al menos 2 caracteres')
    .regex(/^[a-z0-9_-]+$/, 'El slug debe contener solo caracteres alfanuméricos en minúscula, guiones o guiones bajos'),
  sector: z.string().default('Servicios Corporativos'),
  country: z.string().default('España (ES)'),
  currency: z.string().default('EUR (€)'),
  standard: z.string().default('NIS2 / Critical Infrastructure'),
  description: z.string().optional(),
});

export type ClientFormValues = z.infer<typeof clientSchema>;
