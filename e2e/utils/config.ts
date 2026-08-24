import * as path from 'path';

import { env, getEnvironment } from './env';

/** For reports, exports and other large-data screens. */
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
  /** Scoped per user and deployment so a session is never reused across clusters. */
  sessionFile: (safeUserName: string): string => path.join(CACHE_DIR, `${safeUserName}_${getEnvironment()}_SESSION.json`),
} as const;

export const config = {
  ...env,
  timeouts: TIMEOUTS,
  paths,
} as const;
