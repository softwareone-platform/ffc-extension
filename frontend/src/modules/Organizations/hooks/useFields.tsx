import { GridFieldDefinition } from "@swo/design-system/grid";
import { getStatusLabel } from "@swo/mp-status-chip";
import { useFixedT } from "../../../shared/hooks/useFixedT";
import { useMemo } from "react";

export function useFields() {
  const tColumns = useFixedT("shared:grid:columns");
  const tFields = useFixedT("shared:grid:fields");

  return useMemo(
    (): GridFieldDefinition[] => [
      {
        title: tFields("id"),
        name: "id",
      },
      { title: tFields("name"), name: "name" },
      { title: tFields("currency"), name: "currency" },
      { title: tFields("billingCurrency"), name: "billing_currency" },
      { title: tFields("operationsAdditionalId"), name: "operations_external_id" },
      {
        name: "status",
        title: tFields("status"),
        type: "list",
        options: [
          { value: "active", label: getStatusLabel("Active") },
          { value: "new", label: getStatusLabel("New") },
          { value: "terminated", label: getStatusLabel("Terminated") },
          { value: "deleted", label: getStatusLabel("Deleted") }
        ],
      },
    ],
    [tFields],
  );
}
