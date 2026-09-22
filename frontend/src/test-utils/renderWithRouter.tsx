import { ReactElement } from "react";

import { render } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

type Options = {
  initialUrl: string;
  routePath: string;
};

export function renderWithRouter(ui: ReactElement, { initialUrl, routePath }: Options) {
  return render(
    <MemoryRouter initialEntries={[initialUrl]}>
      <Routes>
        <Route path={routePath} element={ui} />
      </Routes>
    </MemoryRouter>,
  );
}
