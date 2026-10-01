import type { ComponentProps } from "react";

import { render, screen } from "@testing-library/react";

import type { AddWizardForm } from "~entitlements/create-entitlement-wizard/CreateEntitlement.Schema";
import type { Status } from "~shared/components/entity-status-chip";
import { mockCustomIcon } from "~test-utils/mocks/customIcon";
import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";

import { EntityProps } from "./EntityProperties";

type EntityReferenceProps = ComponentProps<
  typeof import("@swo/design-system/entity-reference").EntityReference
>;
type StatusProps = ComponentProps<typeof Status<{ status: string }>>;

const mockEntityReference = jest.fn() as jest.MockedFunction<(props: EntityReferenceProps) => void>;
const mockStatus = jest.fn() as jest.MockedFunction<(props: StatusProps) => void>;

jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);
jest.mock("@swo/design-system/text", () => mockDesignSystemText);
jest.mock("./custom-icons/CustomIcon", () => mockCustomIcon);
jest.mock("./entity-status-chip", () => ({
  Status: ({ item }: StatusProps) => {
    mockStatus({ item });
    return <span data-testid="status">{item.status}</span>;
  },
}));
jest.mock("@swo/design-system/entity-reference", () => ({
  EntityReference: ({
    primaryContent,
    secondaryContent,
    isPrimaryContentBold,
    icon,
  }: EntityReferenceProps) => {
    mockEntityReference({ primaryContent, secondaryContent, isPrimaryContentBold, icon });
    return (
      <div data-testid="entity-reference">
        <span data-testid="primary-content">{primaryContent}</span>
        <span data-testid="secondary-content">{secondaryContent}</span>
        <span data-testid="is-primary-content-bold">{String(isPrimaryContentBold)}</span>
        <span data-testid="icon">{icon}</span>
      </div>
    );
  },
}));

function makeEntity(overrides: Partial<AddWizardForm> = {}): AddWizardForm {
  return {
    id: "ent-1",
    name: "Entitlement 1",
    affiliate: {
      id: "aff-1",
      name: "Affiliate 1",
      integration: "aws",
    },
    dataSource: {
      id: "ds-1",
      affiliate_external_id: "ext-1",
    },
    ...overrides,
  } as AddWizardForm;
}

describe("EntityProperties", () => {
  it("renders all properties for a fully populated entity", () => {
    render(<EntityProps entity={makeEntity()} />);

    expect(screen.getAllByTestId("highlight-item")).toHaveLength(4);
    expect(screen.getAllByTestId("highlight-title").map((element) => element.textContent)).toEqual([
      "entitlementId",
      "affiliate",
      "dataSource:id",
      "dataSource:affiliateExternalId",
    ]);
    expect(
      screen.getAllByTestId("secondary-content").map((element) => element.textContent),
    ).toEqual(["ent-1", "aff-1"]);
    expect(screen.getByTestId("custom-icon")).toHaveTextContent("aws");
    expect(screen.getByTestId("status")).toHaveTextContent("New");
    expect(screen.getByText("ds-1")).toBeInTheDocument();
    expect(screen.getByText("ext-1")).toBeInTheDocument();
    expect(mockStatus).toHaveBeenCalledWith({ item: { status: "New" } });
  });

  it("renders fallback values for a draft entity without an affiliate", () => {
    render(
      <EntityProps
        entity={makeEntity({
          id: undefined,
          affiliate: undefined,
          dataSource: { id: "", affiliate_external_id: "" },
        })}
      />,
    );

    expect(screen.getAllByTestId("highlight-item")).toHaveLength(4);
    expect(screen.getAllByTestId("entity-reference")).toHaveLength(1);
    expect(screen.getByTestId("secondary-content")).toHaveTextContent("-");
    expect(screen.getByTestId("status")).toHaveTextContent("Draft");
    expect(screen.queryByTestId("custom-icon")).not.toBeInTheDocument();
    expect(mockStatus).toHaveBeenCalledWith({ item: { status: "Draft" } });
  });
});
