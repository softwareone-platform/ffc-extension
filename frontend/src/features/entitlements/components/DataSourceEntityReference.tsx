import { Avatar } from "@swo/design-system/avatar";
import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";
import { NO_VALUE } from "@swo/design-system/utils";

import CustomIcon from "~shared/components/custom-icons/CustomIcon";

import { Entitlement } from "../api/model";

export function DataSourceEntityReference({ entity }: { readonly entity: Entitlement }) {
  return (
    <EntityReferenceCell
      primaryContent={(entity.linked_datasource_name as string) || NO_VALUE}
      secondaryContent={entity.datasource_id || NO_VALUE}
      secondaryContentMaxHeight={50}
      icon={
        entity.linked_datasource_type ? (
          <CustomIcon name={entity.linked_datasource_type as string} size={48} />
        ) : (
          <Avatar
            text={(entity.datasource_id as string) || NO_VALUE}
            size={48}
            isToUseJdenticon={true}
          />
        )
      }
    />
  );
}
