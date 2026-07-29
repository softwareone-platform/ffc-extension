import { createBrowserRouter, redirect } from "react-router-dom";

import { mountStandaloneEntry } from "~app/bootstrap/mountStandaloneEntry";
import { CloudIqLayout } from "~features/cloud-iq/CloudIqLayout";
import { HelpPage } from "~features/cloud-iq/pages/help/HelpPage";
import { HomePage } from "~features/cloud-iq/pages/home/HomePage";
import { MicrosoftCspPage } from "~features/cloud-iq/pages/microsoft-csp/MicrosoftCspPage";
import { PlaceholderPage } from "~features/cloud-iq/pages/placeholder/PlaceholderPage";
import { TermsAndConditionsPage } from "~features/cloud-iq/pages/terms/TermsAndConditionsPage";
import { PATHS, SEGMENTS } from "~features/cloud-iq/paths";

const router = createBrowserRouter([
  {
    path: PATHS.root,
    element: <CloudIqLayout />,
    children: [
      { index: true, loader: () => redirect(PATHS.home) },
      { path: SEGMENTS.home, element: <HomePage /> },
      { path: SEGMENTS.products, element: <PlaceholderPage title="Products" /> },
      { path: SEGMENTS.microsoftCsp, element: <MicrosoftCspPage /> },
      { path: SEGMENTS.adobe, element: <PlaceholderPage title="Adobe" /> },
      {
        path: SEGMENTS.amazonWebServices,
        element: <PlaceholderPage title="Amazon Web Services" />,
      },
      { path: SEGMENTS.transactions, element: <PlaceholderPage title="Transactions" /> },
      { path: SEGMENTS.insights, element: <PlaceholderPage title="Insights" /> },
      {
        path: SEGMENTS.resellerAdministration,
        element: <PlaceholderPage title="Reseller Administration" />,
      },
      { path: SEGMENTS.support, element: <PlaceholderPage title="Support" /> },
      { path: SEGMENTS.apiIntegrations, element: <PlaceholderPage title="API Integrations" /> },
      { path: SEGMENTS.settings, element: <PlaceholderPage title="Settings" /> },
      { path: SEGMENTS.previousCloudIq, element: <PlaceholderPage title="Previous Cloud-iQ" /> },
      { path: SEGMENTS.help, element: <HelpPage /> },
      { path: SEGMENTS.termsAndConditions, element: <TermsAndConditionsPage /> },
    ],
  },
]);

mountStandaloneEntry(router);
