import { z } from "zod";

export const addProjectSchema = z.object({
  projectName: z.string().min(1),
  companyName: z.string().min(1),
  initialInvestment: z.coerce.number(),
  discountRate: z.coerce.number(),
  hurdleRate: z.coerce.number(),
  scenarioJson: z.string().min(2),
  notes: z.string().optional(),
});

export type AddProjectValues = z.infer<typeof addProjectSchema>;
