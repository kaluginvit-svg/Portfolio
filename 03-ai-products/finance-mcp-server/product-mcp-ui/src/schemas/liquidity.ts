import { z } from "zod";

export const liquidityFormSchema = z.object({
  companyName: z.string().optional(),
  days: z.coerce.number().min(1).max(730).default(90),
});

export type LiquidityFormValues = z.infer<typeof liquidityFormSchema>;
