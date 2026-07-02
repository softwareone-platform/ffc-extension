import { OrganizationRead } from "~api/ffc-api-model";
import { useOrganizationDetailsApi } from "~organizations/api";
import { Status } from "~shared/components/entity-status-chip";
import { PageShell } from "~shared/components/page-shell";

type Props = {
  organizationId: string;
  backUrl: string;
};

export function OrganizationDetailsHeader({ organizationId, backUrl }: Readonly<Props>) {
  const { data: entity } = useOrganizationDetailsApi(organizationId);

  const title = (
    <span>
      {entity?.id}
      {entity?.id && <Status<OrganizationRead> item={entity} />}
    </span>
  );

  return (
    <PageShell.Header
      backUrl={backUrl}
      title={title}
      subtitle={entity?.name ? `Organization ${entity.name}` : "Organization details"}
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
