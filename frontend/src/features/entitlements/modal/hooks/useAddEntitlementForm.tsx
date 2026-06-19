import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { AddEntitlementForm, AddEntitlementFormSchema } from "../AddEntitlementForm.Schema";

export function useAddEntitlementForm(initialData: AddEntitlementForm) {
  return useForm({
    resolver: zodResolver(AddEntitlementFormSchema),
    defaultValues: {
      name: initialData.name,
      description: initialData.description,
      contactEmail: initialData.contactEmail,
    },
    mode: "onChange",
  });
}
