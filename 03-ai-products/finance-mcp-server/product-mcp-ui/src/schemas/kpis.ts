import { z } from "zod";

export const kpiFormSchema = z.object({
  companyName: z.string().optional(),
  periodStart: z.string().optional(),
  periodEnd: z.string().optional(),
});

export type KpiFormValues = z.infer<typeof kpiFormSchema>;
