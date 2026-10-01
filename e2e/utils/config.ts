import * as path from 'path';

import { env } from './env';

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

const originSlug = (url: string): string => new URL(url).host.replace(/[^a-z0-9]+/gi, '_').toLowerCase();

export const paths = {
  cacheDir: CACHE_DIR,
  /** Keyed by origin, so portal.s1.show and portal.s1.today never share a session. */
  sessionFile: (safeUserName: string): string => path.join(CACHE_DIR, `${safeUserName}_${originSlug(env.baseUrl)}_SESSION.json`),
} as const;

export const config = {
  ...env,
  timeouts: TIMEOUTS,
  paths,
} as const;
