export const PARAMS = {
  organizationId: "organizationId",
} as const;

export const SEGMENTS = {
  root: "organizations",
  idParam: `:${PARAMS.organizationId}`,
  general: "general",
  events: "events",
  dataSources: "data-sources",
  users: "users",
  termination: "termination",
} as const;

export const PATHS = {
  root: `/${SEGMENTS.root}`,
  detail: (id: string) => `/${SEGMENTS.root}/${id}`,
  general: (id: string) => `/${SEGMENTS.root}/${id}/${SEGMENTS.general}`,
  events: (id: string) => `/${SEGMENTS.root}/${id}/${SEGMENTS.events}`,
  dataSources: (id: string) => `/${SEGMENTS.root}/${id}/${SEGMENTS.dataSources}`,
  users: (id: string) => `/${SEGMENTS.root}/${id}/${SEGMENTS.users}`,
  termination: (id: string) => `/${SEGMENTS.root}/${id}/${SEGMENTS.termination}`,
  detailMatch: `/${SEGMENTS.root}/${SEGMENTS.idParam}/*`,
} as const;
