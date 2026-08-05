import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { EditOrganizationForm, EditOrganizationFormSchema } from "../EditOrganization.Schema";

export function useEditOrganizationForm(initialData: EditOrganizationForm) {
  return useForm({
    resolver: zodResolver(EditOrganizationFormSchema),
    defaultValues: {
      name: initialData.name,
      operations_external_id: initialData.operations_external_id,
      currency: initialData.currency,
    },
    mode: "onChange",
  });
}
