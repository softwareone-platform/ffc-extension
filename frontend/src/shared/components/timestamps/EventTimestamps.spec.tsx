import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { NO_VALUE, useLocalisation } from "@swo/design-system/utils";

import "./EventTimestamps.spec.mocks";

import { EntityEvent, EventTimestamps } from "./EventTimestamps";

const CREATED: EntityEvent = {
  name: "created",
  by: { id: "usr-1", name: "Alice" },
  at: new Date("2026-01-02T10:00:00Z"),
};
const UPDATED: EntityEvent = {
  name: "updated",
  by: { id: "usr-2", name: "Bob" },
  at: new Date("2026-01-03T11:00:00Z"),
};
const COLUMN_NAMES = ["event", "triggeredBy", "dateAndTime"];

const mockUseLocalisation = jest.mocked(useLocalisation);

function renderTimestamps(events: EntityEvent[], componentTitle?: string) {
  render(
    <EventTimestamps events={events} columnNames={COLUMN_NAMES} componentTitle={componentTitle} />,
  );
}

async function toggle() {
  await userEvent.setup().click(screen.getByTestId("design-system-button"));
}

describe("EventTimestamps", () => {
  beforeEach(() => {
    mockUseLocalisation.mockReturnValue({
      formatDate: (date: Date) => `date:${date.toISOString()}`,
      formatTime: (date: Date) => `time:${date.toISOString()}`,
    } as unknown as ReturnType<typeof useLocalisation>);
  });

  it("renders nothing when there are no events", () => {
    renderTimestamps([], "Events");

    expect(screen.queryByText("Events")).not.toBeInTheDocument();
    expect(screen.queryByTestId("design-system-button")).not.toBeInTheDocument();
  });

  it.each(COLUMN_NAMES)("renders the '%s' column header", (name) => {
    renderTimestamps([CREATED]);

    expect(screen.getByText(name)).toBeInTheDocument();
  });

  it("renders the title when provided", () => {
    renderTimestamps([CREATED], "Events");

    expect(screen.getByRole("heading", { name: "Events" })).toBeInTheDocument();
  });

  it("omits the title when not provided", () => {
    renderTimestamps([CREATED]);

    expect(screen.queryByRole("heading")).not.toBeInTheDocument();
  });

  it("shows only the first event while collapsed", () => {
    renderTimestamps([CREATED, UPDATED]);

    expect(screen.getAllByTestId("event-name")).toHaveLength(1);
    expect(screen.getByTestId("event-name")).toHaveTextContent("created");
    expect(screen.getByTestId("toggle-icon")).toHaveTextContent("arrow_down_keyboard");
  });

  it("shows every event after expanding", async () => {
    renderTimestamps([CREATED, UPDATED]);

    await toggle();

    expect(screen.getAllByTestId("event-name").map((el) => el.textContent)).toEqual([
      "created",
      "updated",
    ]);
    expect(screen.getByTestId("toggle-icon")).toHaveTextContent("arrow_up_keyboard");
  });

  it("returns to the first event after collapsing again", async () => {
    renderTimestamps([CREATED, UPDATED]);

    await toggle();
    await toggle();

    expect(screen.getAllByTestId("event-name")).toHaveLength(1);
    expect(screen.getByTestId("toggle-icon")).toHaveTextContent("arrow_down_keyboard");
  });

  it("renders the actor name, id and avatar alongside the formatted date and time", () => {
    renderTimestamps([CREATED]);

    expect(screen.getAllByTestId("primary-content").map((el) => el.textContent)).toEqual([
      "Alice",
      "date:2026-01-02T10:00:00.000Z",
    ]);
    expect(screen.getAllByTestId("secondary-content").map((el) => el.textContent)).toEqual([
      "usr-1",
      "time:2026-01-02T10:00:00.000Z",
    ]);
    expect(screen.getByTestId("avatar")).toHaveTextContent("usr-1");
  });

  it.each<[string, EntityEvent]>([
    ["actor is missing", { ...CREATED, by: undefined }],
    ["actor has no id", { ...CREATED, by: { id: "", name: "Ghost" } }],
    ["date is missing", { ...CREATED, at: undefined }],
  ])("renders the empty-value placeholder when the %s", (_, event) => {
    renderTimestamps([event]);

    expect(screen.getAllByTestId("entity-reference")).toHaveLength(1);
    expect(screen.getByText(NO_VALUE)).toBeInTheDocument();
  });
});
