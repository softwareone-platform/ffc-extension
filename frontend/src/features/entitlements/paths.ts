export const PARAMS = {
  entitlementId: "entitlementId",
} as const;

export const SEGMENTS = {
  root: "entitlements",
  idParam: `:${PARAMS.entitlementId}`,
  general: "general",
} as const;

export const PATHS = {
  root: `/${SEGMENTS.root}`,
  detail: (id: string) => `/${SEGMENTS.root}/${id}`,
  general: (id: string) => `/${SEGMENTS.root}/${id}/${SEGMENTS.general}`,
  detailMatch: `/${SEGMENTS.root}/${SEGMENTS.idParam}/*`,
} as const;
