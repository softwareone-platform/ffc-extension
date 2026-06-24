export const PARAMS = {
  organizationId: "organizationId",
} as const;

export const SEGMENTS = {
  root: "organizations",
  idParam: `:${PARAMS.organizationId}`,
  general: "general",
  dataSources: "data-sources",
  users: "users",
} as const;

export const PATHS = {
  root: `/${SEGMENTS.root}`,
  detail: (id: string) => `/${SEGMENTS.root}/${id}`,
  general: (id: string) => `/${SEGMENTS.root}/${id}/${SEGMENTS.general}`,
  dataSources: (id: string) => `/${SEGMENTS.root}/${id}/${SEGMENTS.dataSources}`,
  users: (id: string) => `/${SEGMENTS.root}/${id}/${SEGMENTS.users}`,
  detailMatch: `/${SEGMENTS.root}/${SEGMENTS.idParam}/*`,
} as const;
