import { useMemo } from "react";

import { OrganizationRead } from "~api/ffc-api-model/types.gen";
import { SEGMENTS } from "~features/organizations/paths";
import { useFixedT } from "~shared/hooks/useFixedT";

interface UseTopBarItemsProps {
  readonly entity?: OrganizationRead;
  readonly routeId?: string;
  readonly translationKey?: string;
}

export function useTopBarItems({
  entity,
  routeId,
  translationKey = "organization:details",
}: UseTopBarItemsProps) {
  const tDetails = useFixedT(translationKey);

  const dataSourceTopBarItems = [
    { label: tDetails("dataSource:details"), path: `data-sources/${routeId}/details` },
    {
      label: tDetails("dataSource:advanced"),
      path: `data-sources/${routeId}/advanced`,
      isHidden: false,
    },
  ];

  const organizationTopBarItems = useMemo(
    () =>
      [
        { label: tDetails("general:title"), path: SEGMENTS.general },
        {
          label: tDetails("dataSources:title"),
          path: SEGMENTS.dataSources,
          isHidden: entity?.status === "deleted",
        },
        {
          label: tDetails("users:title"),
          path: SEGMENTS.users,
          isHidden: entity?.status === "deleted",
        },
        { label: tDetails("events:title"), path: SEGMENTS.events },
        {
          label: tDetails("termination:title"),
          path: SEGMENTS.termination,
          isHidden: !entity?.termination_feedback?.id,
        },
        {
          label: tDetails("logs:title"),
          path: SEGMENTS.logs,
          isHidden: entity?.status === "deleted",
        },
      ].filter((item) => !item.isHidden),
    [tDetails, entity?.termination_feedback?.id, entity?.status],
  );

  return routeId ? dataSourceTopBarItems : organizationTopBarItems;
}
