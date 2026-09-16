/**
 * Earliest moment a terminated entity is allowed to be deleted: 00:00 (UTC) on the first day of
 * the month following one month after the termination date.
 *
 * e.g. terminated on 2026-01-15 -> +1 month is 2026-02-15 -> deletable from 2026-03-01T00:00:00Z.
 *
 * Returns `null` when there is no usable termination date.
 */
export function getAllowedDeletionDate(terminatedAt?: string | null): Date | null {
  if (!terminatedAt) {
    return null;
  }

  const terminated = new Date(terminatedAt);
  if (Number.isNaN(terminated.getTime())) {
    return null;
  }

  // Date.UTC rolls the month over into the next year on its own.
  return new Date(Date.UTC(terminated.getUTCFullYear(), terminated.getUTCMonth() + 2, 1));
}

/**
 * Whether the deletion grace period following `terminatedAt` has already elapsed.
 */
export function isDeletionAllowed(terminatedAt?: string | null, now: Date = new Date()): boolean {
  const allowedDeletionDate = getAllowedDeletionDate(terminatedAt);

  return allowedDeletionDate !== null && now.getTime() > allowedDeletionDate.getTime();
}

/**
 * Formats a date as an ISO calendar date (`YYYY-MM-DD`).
 *
 * The local date components are used on purpose: the date picker yields local midnight, and
 * `toISOString()` would shift it to the previous day for negative UTC offsets.
 */
export function toIsoDateString(date: Date): string {
  const year = String(date.getFullYear()).padStart(4, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

/**
 * Whether a timestamp means "never happened".
 *
 * Optscale reports a datasource that has never been imported as `0`, which the API serialises as
 * the Unix epoch, so both the epoch and a missing value are treated as "no value".
 */
export function isEpoch(value?: string | number | Date | null): boolean {
  if (value === null || value === undefined || value === "") {
    return true;
  }

  const time = new Date(value).getTime();

  return Number.isNaN(time) || time === 0;
}
