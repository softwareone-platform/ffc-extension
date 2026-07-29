import type { RouteObject } from "react-router-dom";
import { redirect } from "react-router-dom";

import {
  defaultNewsSection,
  defaultTopLevelPath,
  newsSections,
  topLevelSections,
} from "~features/sandboxStandalone/manifest";
import { StandaloneLayout } from "~features/sandboxStandalone/StandaloneLayout";
import { AgreementsPage } from "~features/sandboxStandalone/pages/agreements/AgreementsPage";
import { HelpPage } from "~features/sandboxStandalone/pages/help/HelpPage";
import { NewsMessagesSection, NewsPage } from "~features/sandboxStandalone/pages/news/NewsPage";
import { PlaceholderPage } from "~features/sandboxStandalone/pages/placeholder/PlaceholderPage";
import { ProductsPage } from "~features/sandboxStandalone/pages/products/ProductsPage";
import { TermsAndConditionsPage } from "~features/sandboxStandalone/pages/terms/TermsAndConditionsPage";
import { PATHS } from "~features/sandboxStandalone/paths";

function resolveTopLevelRoute(section: (typeof topLevelSections)[number]): RouteObject {
  if (section.page === "news") {
    return {
      path: section.segment,
      element: <NewsPage />,
      children: [
        { index: true, loader: () => redirect(defaultNewsSection) },
        ...newsSections.filter((entry) => entry.enabled !== false).map((entry) => ({
          path: entry.segment,
          element:
            entry.page === "messages" ? (
              <NewsMessagesSection />
            ) : (
              <PlaceholderPage title={entry.placeholderTitle ?? entry.label} />
            ),
        })),
      ],
    };
  }

  if (section.page === "products") return { path: section.segment, element: <ProductsPage /> };
  if (section.page === "agreements") return { path: section.segment, element: <AgreementsPage /> };
  if (section.page === "help") return { path: section.segment, element: <HelpPage /> };
  if (section.page === "terms") return { path: section.segment, element: <TermsAndConditionsPage /> };

  return {
    path: section.segment,
    element: <PlaceholderPage title={section.placeholderTitle ?? section.path} />,
  };
}

export const sandboxStandaloneRoutes: RouteObject[] = [
  {
    path: PATHS.root,
    element: <StandaloneLayout />,
    children: [
      { index: true, loader: () => redirect(defaultTopLevelPath) },
      ...topLevelSections.filter((section) => section.enabled !== false).map(resolveTopLevelRoute),
    ],
  },
];
