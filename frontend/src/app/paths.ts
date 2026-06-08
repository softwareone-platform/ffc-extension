// Route param names — keys returned from `useParams()` and passed as
// `paramKey` to the shared DetailsLayout.
export const PARAMS = {
  entitlementId: "entitlementId",
  organizationId: "organizationId",
} as const;

// Route segments used inside react-router route definitions and as relative
// `to` targets (e.g. TopBar items).
export const SEGMENTS = {
  entitlements: "entitlements",
  organizations: "organizations",
  general: "general",
  dataSources: "data-sources",
  users: "users",
  entitlementIdParam: `:${PARAMS.entitlementId}`,
  organizationIdParam: `:${PARAMS.organizationId}`,
} as const;

// Absolute paths + builders — one source of truth for every URL the app emits.
export const PATHS = {
  root: "/",
  entitlements: {
    root: `/${SEGMENTS.entitlements}`,
    detail: (id: string) => `/${SEGMENTS.entitlements}/${id}`,
    general: (id: string) => `/${SEGMENTS.entitlements}/${id}/${SEGMENTS.general}`,
    detailMatch: `/${SEGMENTS.entitlements}/${SEGMENTS.entitlementIdParam}/*`,
  },
  organizations: {
    root: `/${SEGMENTS.organizations}`,
    detail: (id: string) => `/${SEGMENTS.organizations}/${id}`,
    general: (id: string) => `/${SEGMENTS.organizations}/${id}/${SEGMENTS.general}`,
    dataSources: (id: string) => `/${SEGMENTS.organizations}/${id}/${SEGMENTS.dataSources}`,
    users: (id: string) => `/${SEGMENTS.organizations}/${id}/${SEGMENTS.users}`,
    detailMatch: `/${SEGMENTS.organizations}/${SEGMENTS.organizationIdParam}/*`,
  },
} as const;
