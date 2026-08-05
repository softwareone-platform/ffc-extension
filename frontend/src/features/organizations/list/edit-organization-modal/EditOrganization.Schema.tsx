import { z } from "zod/v4";

const FULL_NAME_MAX_LENGTH = 255;
const OPERATIONS_EXTERNAL_ID_MAX_LENGTH = 255;
const CURRENCY_MAX_LENGTH = 5;

export const EditOrganizationFormSchema = z.object({
  name: z.string().trim().min(1).max(FULL_NAME_MAX_LENGTH),
  operations_external_id: z.string().trim().min(1).max(OPERATIONS_EXTERNAL_ID_MAX_LENGTH),
  currency: z.string().trim().min(1).max(CURRENCY_MAX_LENGTH),
});

export type EditOrganizationForm = z.output<typeof EditOrganizationFormSchema>;
