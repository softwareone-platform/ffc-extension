const FLAG_KEY_PREFIX = "ffc.flag.";

// Read once at module load, so a flag flipped in devtools applies on the next reload.
function isEnabled(name: string, fallback: boolean): boolean {
  try {
    const stored = localStorage.getItem(FLAG_KEY_PREFIX + name);
    return stored === null ? fallback : stored === "true";
  } catch {
    // The plug iframe has an opaque origin unless the host sandbox grants
    // allow-same-origin, in which case touching localStorage throws.
    return fallback;
  }
}

export const FEATURE_FLAGS = {
  dashboard: isEnabled("dashboard", false),
} as const;
