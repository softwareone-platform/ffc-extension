import type { ComponentProps } from "react";

import { render, screen } from "@testing-library/react";

import { makeEntitlement } from "~test-utils";
import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";
import { mockCustomIcon } from "~test-utils/mocks/sharedGridCells";

import { DataSourceEntityReference } from "./DataSourceEntityReference";

type MockAvatarProps = ComponentProps<typeof import("@swo/design-system/avatar").Avatar>;

jest.mock("@swo/design-system/entity-reference-cell", () => mockEntityReferenceCell);
jest.mock("~shared/components/custom-icons/CustomIcon", () => mockCustomIcon);

jest.mock("@swo/design-system/avatar", () => ({
  Avatar: ({ text }: MockAvatarProps) => <div data-testid="avatar">{text}</div>,
}));

describe("DataSourceEntityReference", () => {
  it("renders the linked_datasource_name as primary and datasource_id as secondary content", () => {
    render(
      <DataSourceEntityReference
        entity={makeEntitlement({
          linked_datasource_name: "AWS Prod",
          datasource_id: "ds-abc",
        })}
      />,
    );

    expect(screen.getByTestId("primary")).toHaveTextContent("AWS Prod");
    expect(screen.getByTestId("secondary")).toHaveTextContent("ds-abc");
  });

  it("falls back to NO_VALUE for primary and secondary when data is missing", () => {
    render(
      <DataSourceEntityReference
        entity={makeEntitlement({
          linked_datasource_name: undefined,
          datasource_id: "",
        })}
      />,
    );

    expect(screen.getByTestId("primary")).toHaveTextContent("—");
    expect(screen.getByTestId("secondary")).toHaveTextContent("—");
  });

  it("renders the linked_datasource_type as a CustomIcon when present", () => {
    render(
      <DataSourceEntityReference
        entity={makeEntitlement({ linked_datasource_type: "azure_cnr" })}
      />,
    );

    expect(screen.getByTestId("custom-icon")).toHaveTextContent("azure_cnr");
    expect(screen.queryByTestId("avatar")).not.toBeInTheDocument();
  });

  it("renders a jdenticon Avatar with datasource_id when linked_datasource_type is missing", () => {
    render(
      <DataSourceEntityReference
        entity={makeEntitlement({
          linked_datasource_type: null,
          datasource_id: "ds-abc",
        })}
      />,
    );

    expect(screen.getByTestId("avatar")).toHaveTextContent("ds-abc");
    expect(screen.queryByTestId("custom-icon")).not.toBeInTheDocument();
  });
});
