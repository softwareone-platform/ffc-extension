import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { AddUserForm, AddUserFormSchema } from "../AddUserForm.Schema";

export function useAddUserForm(initialData: AddUserForm) {
  return useForm({
    resolver: zodResolver(AddUserFormSchema),
    defaultValues: { email: initialData.email, display_name: initialData.display_name },
    mode: "onChange",
  });
}
