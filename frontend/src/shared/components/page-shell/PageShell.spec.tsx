import type { ReactNode } from "react";

import { render, screen } from "@testing-library/react";

import { PageShell } from "./PageShell";

type HeaderBarProps = {
  title?: ReactNode;
  subtitle?: ReactNode;
  backUrl?: string;
  avatar?: unknown;
  items?: Array<{ path: string; label: string }>;
  children?: ReactNode;
};

const mockNavigation = jest.fn() as jest.MockedFunction<(props: { children?: ReactNode }) => void>;
const mockHeaderBar = jest.fn() as jest.MockedFunction<(props: HeaderBarProps) => void>;
const mockHeaderBarActions = jest.fn() as jest.MockedFunction<
  (props: { children?: ReactNode }) => void
>;
const mockContent = jest.fn() as jest.MockedFunction<(props: { children?: ReactNode }) => void>;

jest.mock("@swo/design-system/navigation", () => {
  const Navigation = ({ children }: { children?: ReactNode }) => {
    mockNavigation({ children });
    return <div data-testid="navigation">{children}</div>;
  };

  const HeaderBar = ({ children, ...props }: HeaderBarProps) => {
    mockHeaderBar({ ...props, children });
    return <div data-testid="header-bar">{children}</div>;
  };

  HeaderBar.Actions = ({ children }: { children?: ReactNode }) => {
    mockHeaderBarActions({ children });
    return <div data-testid="header-bar-actions">{children}</div>;
  };
  Navigation.HeaderBar = HeaderBar as typeof Navigation.HeaderBar;

  Navigation.Content = ({ children }: { children?: ReactNode }) => {
    mockContent({ children });
    return <div data-testid="navigation-content">{children}</div>;
  };

  return { Navigation };
});

describe("PageShell", () => {
  beforeEach(() => {
    mockNavigation.mockReset();
    mockHeaderBar.mockReset();
    mockHeaderBarActions.mockReset();
    mockContent.mockReset();
  });

  it("renders children inside the Navigation wrapper", () => {
    render(
      <PageShell>
        <div data-testid="body">body</div>
      </PageShell>,
    );

    expect(screen.getByTestId("navigation")).toHaveTextContent("body");
  });

  it("renders title-mode headers and normalizes null backUrl to undefined", () => {
    render(
      <PageShell.Header
        title="Title"
        subtitle="Subtitle"
        backUrl={null}
        avatar={{} as never}
        actions={<button>action</button>}
      />,
    );

    expect(mockHeaderBar).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Title",
        subtitle: "Subtitle",
        backUrl: undefined,
        avatar: {},
      }),
    );
    expect(screen.getByTestId("header-bar-actions")).toHaveTextContent("action");
  });

  it("renders items-mode headers without actions when none are provided", () => {
    const items = [{ path: "/general", label: "General" }];

    render(<PageShell.Header items={items} />);

    expect(mockHeaderBar).toHaveBeenCalledWith(expect.objectContaining({ items }));
    expect(screen.queryByTestId("header-bar-actions")).not.toBeInTheDocument();
  });

  it("renders content inside Navigation.Content", () => {
    render(
      <PageShell.Content>
        <div data-testid="content-child">content</div>
      </PageShell.Content>,
    );

    expect(screen.getByTestId("navigation-content")).toHaveTextContent("content");
  });
});
