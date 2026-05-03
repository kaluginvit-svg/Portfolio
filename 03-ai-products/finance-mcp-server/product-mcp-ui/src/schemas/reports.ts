import { z } from "zod";

export const exportFormSchema = z.object({
  reportType: z.string().min(1),
  outputFormat: z.enum(["json", "txt"]).default("json"),
  companyName: z.string().optional(),
  periodStart: z.string().optional(),
  periodEnd: z.string().optional(),
  liquidityDays: z.coerce.number().optional().default(90),
  paymentStart: z.string().optional(),
  paymentEnd: z.string().optional(),
  projectId: z.coerce.number().optional(),
});

export type ExportFormValues = z.infer<typeof exportFormSchema>;
