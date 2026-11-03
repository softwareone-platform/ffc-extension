import { DatasourceDetailRead } from "~api/ffc-api-model";
import { CardSection } from "~shared/components/CardSection";
import { useFixedT } from "~shared/hooks/useFixedT";

import { DiscoveryGrid } from "./DiscoveryGrid";

export function Discovery({ entity }: { readonly entity: DatasourceDetailRead }) {
  const tSharedDetails = useFixedT("shared:details");

  return (
    <CardSection title={tSharedDetails("discovery")}>
      <DiscoveryGrid dataSource={entity} />
    </CardSection>
  );
}
