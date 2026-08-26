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
