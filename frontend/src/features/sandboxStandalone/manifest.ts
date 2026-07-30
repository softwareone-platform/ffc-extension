import { NEWS_SECTIONS, PATHS, SEGMENTS } from "~features/sandboxStandalone/paths";

export type NavGroupId = "stayCurrent" | "catalog" | "marketplace" | "billing";

export type TopLevelPageKind =
  | "news"
  | "products"
  | "agreements"
  | "help"
  | "terms"
  | "placeholder";

export type TopLevelSection = {
  segment: string;
  path: string;
  page: TopLevelPageKind;
  placeholderTitle?: string;
  nav?: {
    groupId: NavGroupId;
    label: string;
    enabled?: boolean;
  };
  enabled?: boolean;
};

export type NewsSection = {
  segment: string;
  path: string;
  label: string;
  page: "messages" | "placeholder";
  placeholderTitle?: string;
  enabled?: boolean;
};

export const defaultTopLevelPath = PATHS.newsAndUpdates;
export const defaultNewsSection = NEWS_SECTIONS.messages;

export const navGroupDefinitions = {
  stayCurrent: { label: "Stay current", iconName: "flag", enabled: true },
  catalog: { label: "Catalog", iconName: "category", enabled: true },
  marketplace: { label: "Marketplace", iconName: "storefront", enabled: true },
  billing: { label: "Billing", iconName: "payments", enabled: true },
} as const;

export const topLevelSections: TopLevelSection[] = [
  {
    segment: SEGMENTS.newsAndUpdates,
    path: PATHS.newsAndUpdates,
    page: "news",
    nav: { groupId: "stayCurrent", label: "News and updates", enabled: true },
    enabled: true,
  },
  {
    segment: SEGMENTS.spotlight,
    path: PATHS.spotlight,
    page: "placeholder",
    placeholderTitle: "Spotlight",
    nav: { groupId: "stayCurrent", label: "Spotlight", enabled: true },
    enabled: true,
  },
  {
    segment: SEGMENTS.products,
    path: PATHS.products,
    page: "products",
    nav: { groupId: "catalog", label: "Products", enabled: true },
    enabled: true,
  },
  {
    segment: SEGMENTS.priceLists,
    path: PATHS.priceLists,
    page: "placeholder",
    placeholderTitle: "Price lists",
    nav: { groupId: "catalog", label: "Price lists", enabled: true },
    enabled: true,
  },
  {
    segment: SEGMENTS.agreements,
    path: PATHS.agreements,
    page: "agreements",
    nav: { groupId: "marketplace", label: "Agreements", enabled: true },
    enabled: true,
  },
  {
    segment: SEGMENTS.subscriptions,
    path: PATHS.subscriptions,
    page: "placeholder",
    placeholderTitle: "Subscriptions",
    nav: { groupId: "marketplace", label: "Subscriptions", enabled: true },
    enabled: true,
  },
  {
    segment: SEGMENTS.assets,
    path: PATHS.assets,
    page: "placeholder",
    placeholderTitle: "Assets",
    nav: { groupId: "marketplace", label: "Assets", enabled: true },
    enabled: true,
  },
  {
    segment: SEGMENTS.entitlements,
    path: PATHS.entitlements,
    page: "placeholder",
    placeholderTitle: "Entitlements",
    nav: { groupId: "marketplace", label: "Entitlements", enabled: true },
    enabled: true,
  },
  {
    segment: SEGMENTS.orders,
    path: PATHS.orders,
    page: "placeholder",
    placeholderTitle: "Orders",
    nav: { groupId: "marketplace", label: "Orders", enabled: true },
    enabled: true,
  },
  {
    segment: SEGMENTS.invoices,
    path: PATHS.invoices,
    page: "placeholder",
    placeholderTitle: "Invoices",
    nav: { groupId: "billing", label: "Invoices", enabled: true },
    enabled: true,
  },
  {
    segment: SEGMENTS.creditMemos,
    path: PATHS.creditMemos,
    page: "placeholder",
    placeholderTitle: "Credit Memos",
    nav: { groupId: "billing", label: "Credit Memos", enabled: true },
    enabled: true,
  },
  { segment: SEGMENTS.help, path: PATHS.help, page: "help", enabled: true },
  {
    segment: SEGMENTS.termsAndConditions,
    path: PATHS.termsAndConditions,
    page: "terms",
    enabled: true,
  },
];

export const newsSections: NewsSection[] = [
  {
    segment: NEWS_SECTIONS.messages,
    path: PATHS.newsSection(NEWS_SECTIONS.messages),
    label: "Messages",
    page: "messages",
    enabled: true,
  },
  {
    segment: NEWS_SECTIONS.attachments,
    path: PATHS.newsSection(NEWS_SECTIONS.attachments),
    label: "Attachments",
    page: "placeholder",
    placeholderTitle: "Attachments",
    enabled: true,
  },
  {
    segment: NEWS_SECTIONS.links,
    path: PATHS.newsSection(NEWS_SECTIONS.links),
    label: "Links",
    page: "placeholder",
    placeholderTitle: "Links",
    enabled: true,
  },
  {
    segment: NEWS_SECTIONS.participants,
    path: PATHS.newsSection(NEWS_SECTIONS.participants),
    label: "Participants",
    page: "placeholder",
    placeholderTitle: "Participants",
    enabled: true,
  },
  {
    segment: NEWS_SECTIONS.details,
    path: PATHS.newsSection(NEWS_SECTIONS.details),
    label: "Details",
    page: "placeholder",
    placeholderTitle: "Details",
    enabled: true,
  },
  {
    segment: NEWS_SECTIONS.auditTrail,
    path: PATHS.newsSection(NEWS_SECTIONS.auditTrail),
    label: "Audit trail",
    page: "placeholder",
    placeholderTitle: "Audit trail",
    enabled: true,
  },
];

export const newsHeaderBarItems = newsSections
  .filter((section) => section.enabled !== false)
  .map(({ label, path }) => ({ label, path }));
