import { z } from "zod/v4";

const FULL_NAME_MAX_LENGHT = 255;

export const AddUserFormSchema = z.object({
  email: z.email().nullish(),
  display_name: z.string().trim().max(FULL_NAME_MAX_LENGHT).nullish(),
});

export type AddUserForm = z.output<typeof AddUserFormSchema>;
