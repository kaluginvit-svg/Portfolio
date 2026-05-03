import { z } from "zod";

export const importFormSchema = z.object({
  statementType: z.string().min(1),
  companyName: z.string().optional(),
  version: z.string().optional(),
});

export type ImportFormValues = z.infer<typeof importFormSchema>;
