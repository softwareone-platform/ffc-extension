import type { ComponentProps } from "react";

import type { EntityReference } from "@swo/design-system/entity-reference";

export type MockEntityReferenceProps = ComponentProps<typeof EntityReference>;

export const mockEntityReference = jest.fn() as jest.MockedFunction<
  (props: MockEntityReferenceProps) => void
>;

export const mockDesignSystemEntityReference = {
  EntityReference: (props: MockEntityReferenceProps) => {
    mockEntityReference(props);
    const { primaryContent, secondaryContent, isPrimaryContentBold, icon } = props;

    return (
      <div data-testid="entity-reference">
        <span data-testid="primary-content">{primaryContent}</span>
        <span data-testid="secondary-content">{secondaryContent}</span>
        <span data-testid="is-primary-content-bold">{String(isPrimaryContentBold)}</span>
        <span data-testid="icon">{icon}</span>
      </div>
    );
  },
};
