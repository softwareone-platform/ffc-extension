import { z } from "zod/v4";

const FULL_NAME_MAX_LENGTH = 255;

export const AddUserFormSchema = z.object({
  email: z.email(),
  display_name: z.string().trim().min(1).max(FULL_NAME_MAX_LENGTH),
});

export type AddUserForm = z.output<typeof AddUserFormSchema>;
