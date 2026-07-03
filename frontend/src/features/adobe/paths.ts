export const SEGMENTS = {
  newsAndUpdates: "news-and-updates",
  spotlight: "spotlight",
  products: "products",
  priceLists: "price-lists",
  agreements: "agreements",
  subscriptions: "subscriptions",
  assets: "assets",
  entitlements: "entitlements",
  orders: "orders",
  invoices: "invoices",
  creditMemos: "credit-memos",
} as const;

export const NEWS_SECTIONS = {
  messages: "messages",
  attachments: "attachments",
  links: "links",
  participants: "participants",
  details: "details",
  auditTrail: "audit-trail",
} as const;

export const PATHS = {
  root: "/",
  newsAndUpdates: `/${SEGMENTS.newsAndUpdates}`,
  newsSection: (section: (typeof NEWS_SECTIONS)[keyof typeof NEWS_SECTIONS]) =>
    `/${SEGMENTS.newsAndUpdates}/${section}`,
  spotlight: `/${SEGMENTS.spotlight}`,
  products: `/${SEGMENTS.products}`,
  priceLists: `/${SEGMENTS.priceLists}`,
  agreements: `/${SEGMENTS.agreements}`,
  subscriptions: `/${SEGMENTS.subscriptions}`,
  assets: `/${SEGMENTS.assets}`,
  entitlements: `/${SEGMENTS.entitlements}`,
  orders: `/${SEGMENTS.orders}`,
  invoices: `/${SEGMENTS.invoices}`,
  creditMemos: `/${SEGMENTS.creditMemos}`,
} as const;
