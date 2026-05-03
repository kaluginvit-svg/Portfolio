import { z } from "zod";

export const toolRequestSchema = z.object({
  tool: z.string().min(1),
  payload: z.record(z.any()).optional().default({}),
});
