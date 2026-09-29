// Global mock for react-router-dom — pass everything through to the real module
// EXCEPT Link, which we stub to render children only (avoids Router context in
// specs that render an isolated component). Auto-discovered by Jest because
// this file lives adjacent to node_modules.
import type { ReactNode } from "react";

const actual = jest.requireActual("react-router-dom");

module.exports = {
  ...actual,
  Link: ({ children }: { children: ReactNode }) => <>{children}</>,
};
