import type { ReactElement } from "react";

import { setup } from "@mpt-extension/sdk";

const mockSafeStorage = jest.fn();
const mockRender = jest.fn();
const mockCreateRoot = jest.fn((_element: Element) => ({
  render: mockRender,
  unmount: jest.fn(),
}));
const AppStub = () => null;
const ExtensionsProviderStub = (props: { i18n: unknown; children?: unknown }) =>
  props.children as ReactElement;
const fakeI18n = { changeLanguage: jest.fn() };

jest.mock("~fixes/safe-storage", () => {
  mockSafeStorage();
  return {};
});

jest.mock("react-dom/client", () => ({
  createRoot: (element: Element) => mockCreateRoot(element),
}));

jest.mock("~app/App", () => ({ App: AppStub }));

jest.mock("~i18n/translations", () => ({ i18n: fakeI18n }));

jest.mock("~shared/providers/ExtensionsProvider", () => ({
  ExtensionsProvider: ExtensionsProviderStub,
}));

const mockSetup = setup as jest.MockedFunction<typeof setup>;

describe("StandaloneRoot bootstrap", () => {
  beforeEach(() => {
    jest.isolateModules(() => {
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      require("./StandaloneRoot");
    });
  });

  it("runs the safe-storage side-effect import", () => {
    expect(mockSafeStorage).toHaveBeenCalled();
  });

  it("registers a single mount callback with @mpt-extension/sdk setup", () => {
    expect(mockSetup).toHaveBeenCalledTimes(1);
    expect(mockSetup.mock.lastCall![0]).toEqual(expect.any(Function));
  });

  describe("mount callback", () => {
    const element = document.createElement("div");
    let renderedTree: ReactElement;

    beforeEach(() => {
      const mount = mockSetup.mock.lastCall![0] as (element: Element) => void;
      mount(element);
      renderedTree = mockRender.mock.lastCall![0] as ReactElement;
    });

    it("creates a React root on the supplied element", () => {
      expect(mockCreateRoot).toHaveBeenCalledWith(element);
    });

    it("renders exactly once through the created root", () => {
      expect(mockRender).toHaveBeenCalledTimes(1);
    });

    it("wraps the tree in ExtensionsProvider and passes the i18n instance", () => {
      expect(renderedTree.type).toBe(ExtensionsProviderStub);
      expect((renderedTree.props as { i18n: unknown }).i18n).toBe(fakeI18n);
    });

    it("renders App as the ExtensionsProvider child", () => {
      const child = (renderedTree.props as { children: ReactElement }).children;
      expect(child.type).toBe(AppStub);
    });
  });
});
