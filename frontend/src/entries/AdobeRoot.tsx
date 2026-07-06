import { createBrowserRouter, redirect } from "react-router-dom";

import { mountStandaloneEntry } from "~app/bootstrap/mountStandaloneEntry";
import { AdobeLayout } from "~features/adobe/AdobeLayout";
import { AgreementsPage } from "~features/adobe/pages/agreements/AgreementsPage";
import { HelpPage } from "~features/adobe/pages/help/HelpPage";
import { NewsMessagesSection, NewsPage } from "~features/adobe/pages/news/NewsPage";
import { PlaceholderPage } from "~features/adobe/pages/placeholder/PlaceholderPage";
import { ProductsPage } from "~features/adobe/pages/products/ProductsPage";
import { TermsAndConditionsPage } from "~features/adobe/pages/terms/TermsAndConditionsPage";
import { NEWS_SECTIONS, PATHS, SEGMENTS } from "~features/adobe/paths";

const router = createBrowserRouter([
  {
    path: PATHS.root,
    element: <AdobeLayout />,
    children: [
      { index: true, loader: () => redirect(PATHS.newsAndUpdates) },
      {
        path: SEGMENTS.newsAndUpdates,
        element: <NewsPage />,
        children: [
          { index: true, loader: () => redirect(NEWS_SECTIONS.messages) },
          { path: NEWS_SECTIONS.messages, element: <NewsMessagesSection /> },
          { path: NEWS_SECTIONS.attachments, element: <PlaceholderPage title="Attachments" /> },
          { path: NEWS_SECTIONS.links, element: <PlaceholderPage title="Links" /> },
          { path: NEWS_SECTIONS.participants, element: <PlaceholderPage title="Participants" /> },
          { path: NEWS_SECTIONS.details, element: <PlaceholderPage title="Details" /> },
          { path: NEWS_SECTIONS.auditTrail, element: <PlaceholderPage title="Audit trail" /> },
        ],
      },
      { path: SEGMENTS.spotlight, element: <PlaceholderPage title="Spotlight" /> },
      { path: SEGMENTS.products, element: <ProductsPage /> },
      { path: SEGMENTS.priceLists, element: <PlaceholderPage title="Price lists" /> },
      { path: SEGMENTS.agreements, element: <AgreementsPage /> },
      { path: SEGMENTS.subscriptions, element: <PlaceholderPage title="Subscriptions" /> },
      { path: SEGMENTS.assets, element: <PlaceholderPage title="Assets" /> },
      { path: SEGMENTS.entitlements, element: <PlaceholderPage title="Entitlements" /> },
      { path: SEGMENTS.orders, element: <PlaceholderPage title="Orders" /> },
      { path: SEGMENTS.invoices, element: <PlaceholderPage title="Invoices" /> },
      { path: SEGMENTS.creditMemos, element: <PlaceholderPage title="Credit Memos" /> },
      { path: SEGMENTS.help, element: <HelpPage /> },
      { path: SEGMENTS.termsAndConditions, element: <TermsAndConditionsPage /> },
    ],
  },
]);

mountStandaloneEntry(router);
