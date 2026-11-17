import { screen, within } from "@testing-library/react";

// Reads every item rendered by `~test-utils/mocks/inPageHighlight` into a
// `{ [title]: value }` map, so specs can assert on a highlight by its title.
export function highlightValues(): Record<string, string> {
  return Object.fromEntries(
    screen
      .getAllByTestId("highlight-item")
      .map((item) => [
        within(item).getByTestId("highlight-title").textContent ?? "",
        within(item).getByTestId("highlight-value").textContent ?? "",
      ]),
  );
}
