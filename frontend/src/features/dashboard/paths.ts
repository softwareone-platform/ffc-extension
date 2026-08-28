export const SEGMENTS = {
  root: "dashboard",
  adoption: "adoption",
  consumption: "consumption",
  health: "health",
  maturity: "maturity",
} as const;

export const PATHS = {
  root: `/${SEGMENTS.root}`,
  adoption: `/${SEGMENTS.root}/${SEGMENTS.adoption}`,
  consumption: `/${SEGMENTS.root}/${SEGMENTS.consumption}`,
  health: `/${SEGMENTS.root}/${SEGMENTS.health}`,
  maturity: `/${SEGMENTS.root}/${SEGMENTS.maturity}`,
} as const;
