import { ReactNode } from "react";

export const mockEntityReferenceCell = {
  EntityReferenceCell: ({
    primaryContent,
    secondaryContent,
    icon,
  }: {
    primaryContent: ReactNode;
    secondaryContent: ReactNode;
    icon: ReactNode;
  }) => (
    <div data-testid="entity-reference-cell">
      <span data-testid="primary">{primaryContent}</span>
      <span data-testid="secondary">{secondaryContent}</span>
      <span data-testid="icon">{icon}</span>
    </div>
  ),
};
