import { createBrowserRouter } from "react-router-dom";

import { mountStandaloneEntry } from "~app/bootstrap/mountStandaloneEntry";
import { sandboxStandaloneRoutes } from "~features/sandboxStanalone/routes";

const router = createBrowserRouter(sandboxStandaloneRoutes);

mountStandaloneEntry(router);
