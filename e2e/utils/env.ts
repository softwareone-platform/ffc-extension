import * as dotenv from 'dotenv';
import * as fs from 'fs';
import * as path from 'path';

import { ENVIRONMENTS, ENVIRONMENT_KEYS } from '../env.config';
import { EnvironmentConfig } from '../types/environment';

// Loaded here so every importer sees the files, whatever the import order.
dotenv.config({ path: path.resolve(__dirname, '..', '.env.local') });

const localTestEnv = process.env.LOCAL_TEST_ENV;
if (localTestEnv) {
  const envPath = path.resolve(__dirname, '..', `.env.${localTestEnv}`);
  if (!fs.existsSync(envPath)) {
    throw new Error(`LOCAL_TEST_ENV=${localTestEnv} but no env file at ${envPath}`);
  }
  dotenv.config({ path: envPath });
}

const asBool = (value: string | undefined, fallback = false): boolean => (value === undefined ? fallback : value === 'true');

const asString = (value: string | undefined, fallback: string): string => (value !== undefined && value.length > 0 ? value : fallback);

const asPositiveInt = (value: string | undefined, fallback: number): number => {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
};

const asEnum = <T extends string>(name: string, value: string | undefined, allowed: readonly T[]): T => {
  const resolved = value?.toUpperCase() as T | undefined;
  if (resolved !== undefined && allowed.includes(resolved)) return resolved;
  throw new Error(
    `Unknown ${name} "${value ?? ''}". Expected one of: ${allowed.join(', ')}. ` +
      `Set ENVIRONMENT (or LOCAL_TEST_ENV) to choose the target deployment.`
  );
};

// No invented default: an unset or typo'd value fails loudly instead of hitting TEST.
const testEnv = asEnum('ENVIRONMENT', process.env.ENVIRONMENT ?? localTestEnv, ENVIRONMENT_KEYS);

export const env = {
  testEnv,
  baseUrl: ENVIRONMENTS[testEnv].baseUrl,
  ffcClientBaseUrl: ENVIRONMENTS[testEnv].ffcClientBaseUrl,
  defaultUserPassword: asString(process.env.DEFAULT_USER_PASSWORD, ''),
  isCI: asBool(process.env.CI),
  workers: asPositiveInt(process.env.PW_WORKERS, 3),
  ignoreHttpsErrors: asBool(process.env.IGNORE_HTTPS_ERRORS),
  debugLog: asBool(process.env.DEBUG_LOG),
  browserErrorLogging: asBool(process.env.BROWSER_ERROR_LOGGING),
  cleanUp: asBool(process.env.CLEAN_UP),
} as const;

type Env = typeof env;

// Spelled out, not derived: irregulars like isCI -> CI.
const ENV_VAR_NAMES: Record<keyof Env, string> = {
  testEnv: 'ENVIRONMENT',
  baseUrl: 'ENVIRONMENT',
  ffcClientBaseUrl: 'ENVIRONMENT',
  defaultUserPassword: 'DEFAULT_USER_PASSWORD',
  isCI: 'CI',
  workers: 'PW_WORKERS',
  ignoreHttpsErrors: 'IGNORE_HTTPS_ERRORS',
  debugLog: 'DEBUG_LOG',
  browserErrorLogging: 'BROWSER_ERROR_LOGGING',
  cleanUp: 'CLEAN_UP',
};

/** Call where the value is used, so a missing var names itself. */
export function requireEnv(...keys: Array<keyof Env>): void {
  const missing = keys.filter(key => !env[key]);
  if (missing.length === 0) return;

  const names = missing.map(key => ENV_VAR_NAMES[key]).join(', ');
  throw new Error(`Missing required env var${missing.length > 1 ? 's' : ''}: ${names}`);
}

export function getCurrentEnv(): EnvironmentConfig {
  return ENVIRONMENTS[testEnv];
}
