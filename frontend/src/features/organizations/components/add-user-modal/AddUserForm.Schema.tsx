import { z } from "zod/v4";

const FULL_NAME_MAX_LENGTH = 255;

export const AddUserFormSchema = z.object({
  email: z.email().nullish(),
  display_name: z.string().trim().max(FULL_NAME_MAX_LENGTH).nullish(),
});

export type AddUserForm = z.output<typeof AddUserFormSchema>;
