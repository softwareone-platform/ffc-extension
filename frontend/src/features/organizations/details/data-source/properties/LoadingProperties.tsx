import { Skeleton } from "@swo/design-system/skeleton";

import { CardSection } from "~shared/components/CardSection";
import { useFixedT } from "~shared/hooks/useFixedT";

export function LoadingDataSourceProperties({ title }: { readonly title?: string }) {
  const tSharedDetails = useFixedT("shared:details");

  return (
    <CardSection title={title || tSharedDetails("properties")}>
      <Skeleton rows={1} cols={1} />
    </CardSection>
  );
}
