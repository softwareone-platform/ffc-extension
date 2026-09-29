import type { ComponentProps } from "react";

import type { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";

type MockEntityReferenceCellProps = Pick<
  ComponentProps<typeof EntityReferenceCell>,
  "primaryContent" | "secondaryContent" | "icon"
>;

export const mockEntityReferenceCell = {
  EntityReferenceCell: ({
    primaryContent,
    secondaryContent,
    icon,
  }: MockEntityReferenceCellProps) => (
    <div data-testid="entity-reference-cell">
      <span data-testid="primary">{primaryContent}</span>
      <span data-testid="secondary">{secondaryContent}</span>
      <span data-testid="icon">{icon}</span>
    </div>
  ),
};
