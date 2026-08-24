import * as path from 'path';

import { env, getEnvironment } from './env';

/**
 * Extended timeout (ms) for operations that load large amounts of data,
 * such as reports, exports, or pages with many resources.
 */
export const LARGE_DATA_TIMEOUT = 30_000;

export const TIMEOUTS = {
  action: 10_000,
  expect: 15_000,
  test: 90_000,
  largeData: LARGE_DATA_TIMEOUT,
  login: 60_000,
} as const;

const CACHE_DIR = path.resolve(__dirname, '..', '.cache');

export const paths = {
  cacheDir: CACHE_DIR,
  /** Session state is scoped per user *and* deployment so a cached login is never reused across clusters. */
  sessionFile: (safeUserName: string): string => path.join(CACHE_DIR, `${safeUserName}_${getEnvironment()}_SESSION.json`),
} as const;

export const config = {
  ...env,
  timeouts: TIMEOUTS,
  paths,
} as const;
