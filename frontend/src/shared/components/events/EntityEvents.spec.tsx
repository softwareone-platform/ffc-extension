import type { ComponentProps } from "react";

import { render, screen } from "@testing-library/react";

import type { AuditEventsSchema } from "~api/ffc-api-model";
import type { EventTimestamps } from "~shared/components/timestamps/EventTimestamps";
import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";

import { EntityEvents } from "./EntityEvents";

type EventTimestampsProps = ComponentProps<typeof EventTimestamps>;

const mockEventTimestamps = jest.fn() as jest.MockedFunction<(props: EventTimestampsProps) => void>;

jest.mock("@swo/design-system/text", () => mockDesignSystemText);
jest.mock("~shared/components/timestamps/EventTimestamps", () => ({
  EventTimestamps: (props: EventTimestampsProps) => {
    mockEventTimestamps(props);
    return null;
  },
}));

function renderEvents(events: Partial<AuditEventsSchema> | undefined) {
  render(<EntityEvents entity={{ events: events as AuditEventsSchema }} />);
}

describe("EntityEvents", () => {
  it("renders the events section title", () => {
    renderEvents({});

    expect(screen.getByText("events")).toBeInTheDocument();
  });

  it("renders the timestamp column names", () => {
    renderEvents({});

    expect(mockEventTimestamps.mock.lastCall![0].columnNames).toEqual([
      "event",
      "triggeredBy",
      "dateAndTime",
    ]);
  });

  it("lists only events that have a timestamp", () => {
    renderEvents({
      created: { at: "2026-01-02T10:00:00Z", by: { id: "usr-1", type: "user", name: "Alice" } },
      deleted: { at: "", by: { id: "usr-2", type: "user", name: "Bob" } },
    });

    expect(mockEventTimestamps.mock.lastCall![0].events).toEqual([
      {
        name: "created",
        by: { id: "usr-1", type: "user", name: "Alice" },
        at: new Date("2026-01-02T10:00:00Z"),
      },
    ]);
  });

  it("attributes events without an actor to the system", () => {
    renderEvents({ updated: { at: "2026-01-03T11:00:00Z", by: null } });

    expect(mockEventTimestamps.mock.lastCall![0].events).toEqual([
      {
        name: "updated",
        by: { id: "system", name: "system" },
        at: new Date("2026-01-03T11:00:00Z"),
      },
    ]);
  });

  it("lists no events when the entity has no events", () => {
    renderEvents(undefined);

    expect(mockEventTimestamps.mock.lastCall![0].events).toEqual([]);
  });
});
