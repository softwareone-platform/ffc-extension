import { createBrowserRouter } from "react-router-dom";

import { mountStandaloneEntry } from "~app/bootstrap/mountStandaloneEntry";
import { sandboxStandaloneRoutes } from "~features/sandboxStandalone/routes";

const router = createBrowserRouter(sandboxStandaloneRoutes);

mountStandaloneEntry(router);
