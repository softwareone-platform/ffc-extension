import type { PropsWithChildren } from "react";

import { renderHook } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { ContentType, useContentType } from "./useContentType";

function renderContentType(initialUrl: string, routePath: string) {
  function RouterWrapper({ children }: PropsWithChildren) {
    return (
      <MemoryRouter initialEntries={[initialUrl]}>
        <Routes>
          <Route path={routePath} element={children} />
        </Routes>
      </MemoryRouter>
    );
  }

  return renderHook(() => useContentType(), { wrapper: RouterWrapper });
}

describe("useContentType", () => {
  it.each([
    [
      "data source",
      "/organizations/org-1/data-sources/ds-1/details",
      "/organizations/:organizationId/data-sources/:dataSourceId/*",
      ContentType.DataSource,
    ],
    [
      "organization",
      "/organizations/org-1/general",
      "/organizations/:organizationId/*",
      ContentType.Organization,
    ],
    ["unknown", "/organizations", "/organizations", ContentType.Unknown],
  ])("resolves the %s content type from the route params", (_, initialUrl, routePath, expected) => {
    const { result } = renderContentType(initialUrl, routePath);

    expect(result.current).toBe(expected);
  });
});
