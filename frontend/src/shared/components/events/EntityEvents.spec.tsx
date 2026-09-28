import type { ComponentProps } from "react";

import { render, screen } from "@testing-library/react";

import type { AuditEventsSchema } from "~api/ffc-api-model/types.gen";
import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";

import { EntityEvents } from "./EntityEvents";

type EntityReferenceProps = ComponentProps<
  typeof import("@swo/design-system/entity-reference").EntityReference
>;

const mockEntityReference = jest.fn() as jest.MockedFunction<(props: EntityReferenceProps) => void>;

jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);
jest.mock("@swo/design-system/text", () => mockDesignSystemText);
jest.mock("@swo/design-system/entity-reference", () => ({
  EntityReference: ({
    primaryContent,
    secondaryContent,
    isPrimaryContentBold,
  }: EntityReferenceProps) => {
    mockEntityReference({ primaryContent, secondaryContent, isPrimaryContentBold });
    return (
      <div data-testid="entity-reference">
        <span data-testid="primary-content">{primaryContent}</span>
        <span data-testid="secondary-content">{secondaryContent}</span>
      </div>
    );
  },
}));

function makeEntity(events: Partial<AuditEventsSchema>): { events: AuditEventsSchema } {
  return { events: events as AuditEventsSchema };
}

describe("EntityEvents", () => {
  it("renders only events with timestamps and falls back to the system actor", () => {
    render(
      <EntityEvents
        entity={makeEntity({
          created: {
            at: "2026-01-02T10:00:00Z",
            by: { id: "usr-1", type: "user", name: "Alice" },
          },
          updated: {
            at: "2026-01-03T11:00:00Z",
            by: null,
          },
          deleted: {
            at: "",
            by: { id: "usr-2", type: "user", name: "Bob" },
          },
        })}
      />,
    );

    expect(screen.getByText("events")).toBeInTheDocument();
    expect(screen.getAllByTestId("highlight-item")).toHaveLength(2);
    expect(screen.getAllByTestId("highlight-title").map((element) => element.textContent)).toEqual([
      "created",
      "updated",
    ]);
    expect(screen.getAllByTestId("primary-content").map((element) => element.textContent)).toEqual([
      "Alice",
      "system",
    ]);
    expect(
      screen.getAllByTestId("secondary-content").map((element) => element.textContent),
    ).toEqual(["2026-01-02T10:00:00Z", "2026-01-03T11:00:00Z"]);
    expect(mockEntityReference).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        primaryContent: "system",
        secondaryContent: "2026-01-03T11:00:00Z",
        isPrimaryContentBold: true,
      }),
    );
  });

  it("renders an empty event list when the entity has no events", () => {
    render(<EntityEvents entity={{ events: undefined } as never} />);

    expect(screen.getByText("events")).toBeInTheDocument();
    expect(screen.queryByTestId("highlight-item")).not.toBeInTheDocument();
    expect(mockEntityReference).not.toHaveBeenCalled();
  });
});
