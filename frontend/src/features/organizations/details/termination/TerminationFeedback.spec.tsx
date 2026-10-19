import { screen } from "@testing-library/react";

import type { OrganizationRead } from "~api/ffc-api-model";
import type { useOrganizationDetailsApi } from "~organizations/api";
import { makeOrganization, renderWithOrganizationRoute } from "~test-utils";
import { mockDesignSystemNotification } from "~test-utils/mocks/designSystemNotification";
import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";
import { mockDesignSystemUtils } from "~test-utils/mocks/designSystemUtils";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";

import { OrganizationTerminationFeedback } from "./TerminationFeedback";

type ApiResult = ReturnType<typeof useOrganizationDetailsApi>;
type TerminationFeedback = NonNullable<OrganizationRead["termination_feedback"]>;

const mockUseOrganizationDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useOrganizationDetailsApi
>;

jest.mock("~organizations/api", () => ({
  useOrganizationDetailsApi: (id: string | undefined) => mockUseOrganizationDetailsApi(id),
}));

jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);

jest.mock("@swo/design-system/notification", () => mockDesignSystemNotification);

jest.mock("@swo/design-system/text", () => mockDesignSystemText);

jest.mock("@swo/design-system/utils", () => mockDesignSystemUtils);

function primeEntity(entity: OrganizationRead | undefined) {
  mockUseOrganizationDetailsApi.mockReturnValue({ data: entity } as unknown as ApiResult);
}

function primeFeedback(feedback: Partial<TerminationFeedback>) {
  primeEntity(
    makeOrganization({
      termination_feedback: { id: "tf-1", reason: "too_complex", ...feedback },
    }),
  );
}

function highlightValues() {
  return screen.getAllByTestId("highlight-value").map((el) => el.textContent);
}

describe("OrganizationTerminationFeedback", () => {
  it("queries organization details using the organizationId route param", () => {
    primeEntity(undefined);

    renderWithOrganizationRoute(<OrganizationTerminationFeedback />);

    expect(mockUseOrganizationDetailsApi).toHaveBeenCalledWith("org-1");
  });

  it("renders the section title", () => {
    primeEntity(undefined);

    renderWithOrganizationRoute(<OrganizationTerminationFeedback />);

    expect(screen.getByText("title")).toBeInTheDocument();
  });

  it("renders the reason and comment from the termination feedback", () => {
    primeFeedback({ reason: "cost_or_pricing", comments: "Too expensive" });

    renderWithOrganizationRoute(<OrganizationTerminationFeedback />);

    const titles = screen.getAllByTestId("highlight-title").map((el) => el.textContent);
    expect(titles).toEqual(["reason", "comment"]);
    expect(highlightValues()).toEqual(["cost_or_pricing", "Too expensive"]);
    expect(screen.queryByTestId("inline-notification")).not.toBeInTheDocument();
  });

  it("falls back to the unknown reason when the reason is missing", () => {
    primeFeedback({ reason: undefined, comments: "No reason given" });

    renderWithOrganizationRoute(<OrganizationTerminationFeedback />);

    expect(highlightValues()).toEqual(["unknown", "No reason given"]);
  });

  it("renders an empty comment when the comments are null", () => {
    primeFeedback({ reason: "other", comments: null });

    renderWithOrganizationRoute(<OrganizationTerminationFeedback />);

    expect(highlightValues()).toEqual(["other", ""]);
  });

  it.each([
    ["the organization is not loaded", undefined],
    [
      "the organization has no termination feedback",
      makeOrganization({ termination_feedback: null }),
    ],
  ])("shows the missing-feedback warning when %s", (_, entity) => {
    primeEntity(entity);

    renderWithOrganizationRoute(<OrganizationTerminationFeedback />);

    expect(screen.getByTestId("inline-notification")).toHaveTextContent("feedbackMissing");
    expect(screen.queryByTestId("in-page-highlight")).not.toBeInTheDocument();
  });
});
