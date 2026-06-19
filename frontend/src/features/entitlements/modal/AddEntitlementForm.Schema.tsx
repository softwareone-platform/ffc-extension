import { z } from "zod/v4";

const NAME_MAX_LENGTH = 255;

export const AddEntitlementFormSchema = z.object({
  name: z.string().trim().min(1).max(NAME_MAX_LENGTH),
  description: z.string().trim().max(NAME_MAX_LENGTH).optional(),
  contactEmail: z.union([z.email(), z.literal("")]).optional(),
});

export type AddEntitlementForm = z.output<typeof AddEntitlementFormSchema>;
