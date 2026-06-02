import { EntitlementRead } from "@swo/ffc-api-model";

import { useEntitlementsDetailsApi } from "~entitlements/api";
import { Status } from "~shared/components/entity-status-chip";
import { PageShell } from "~shared/components/page-shell";

type Props = {
  entitlementId: string;
  backUrl: string;
};

export function EntitlementDetailsHeader({ entitlementId, backUrl }: Props) {
  const { data: entity } = useEntitlementsDetailsApi(entitlementId);

  const title = (
    <span>
      {entity?.id}
      {entity?.id && <Status<EntitlementRead> item={entity} />}
    </span>
  );

  return (
    <PageShell.Header
      backUrl={backUrl}
      title={title}
      subtitle={entity?.name ? `Entitlement ${entity.name}` : "Entitlement details"}
      avatar={{
        type: "text",
        shape: "circle",
        text: entity?.name ?? "?",
        isToUseJdenticon: true,
        jdenticonValue: entity?.id ?? entity?.name ?? "",
      }}
    />
  );
}
