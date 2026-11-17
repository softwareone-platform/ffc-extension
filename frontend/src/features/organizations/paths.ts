export const PARAMS = {
  organizationId: "organizationId",
  dataSourceId: "dataSourceId",
} as const;

// Query params the list reads on load, so another feature can deep-link a filtered list.
export const LIST_PARAMS = {
  statuses: "statuses",
} as const;

export const SEGMENTS = {
  root: "organizations",
  idParam: `:${PARAMS.organizationId}`,
  dataSourceId: `:${PARAMS.dataSourceId}`,
  general: "general",
  events: "events",
  dataSources: "data-sources",
  users: "users",
  termination: "termination",
  logs: "logs",
  dataSourceDetails: "details",
  dataSourceAdvanced: "advanced",
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
  dataSourceMatch: `/${SEGMENTS.root}/${SEGMENTS.idParam}/data-sources/${SEGMENTS.dataSourceId}/*`,
} as const;
