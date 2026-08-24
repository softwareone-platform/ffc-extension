import { devEnvironmentData } from './test-data/env-data/devEnvironmentData';
import { testEnvironmentData } from './test-data/env-data/testEnvironmentData';
import { TestData } from './types/TestData';
import { EEnvironment } from './types/enums';

export const ENVIRONMENT_KEYS = [EEnvironment.TEST, EEnvironment.DEV] as const;

export type EnvironmentKey = (typeof ENVIRONMENT_KEYS)[number];

export const ENVIRONMENTS = {
  [EEnvironment.TEST]: testEnvironmentData,
  [EEnvironment.DEV]: devEnvironmentData,
} as const satisfies Record<EnvironmentKey, TestData>;

const BARE_ORIGIN_PATTERN = /^https:\/\/[a-z0-9]([a-z0-9.-]*[a-z0-9])?(?::\d{1,5})?$/i;

export const isBareOrigin = (value: string): boolean => BARE_ORIGIN_PATTERN.test(value);

// Import-time: a bad definition fails before the first test.
function assertEnvironmentsAreValid(): void {
  const problems: string[] = [];

  for (const key of ENVIRONMENT_KEYS) {
    const data = ENVIRONMENTS[key];

    // A mismatch would report one environment while targeting another.
    if (data.name !== key) {
      problems.push(`ENVIRONMENTS.${key}.name must be "${key}" — got "${data.name}"`);
    }

    for (const field of ['baseUrl', 'ffcClientBaseUrl'] as const) {
      const url = data[field];
      if (!isBareOrigin(url)) {
        problems.push(`${key}.${field} must be https://host[:port] with no trailing slash — got "${url}"`);
      }
    }
  }

  if (problems.length > 0) {
    throw new Error(`Invalid environment definitions in env.config.ts:\n  - ${problems.join('\n  - ')}`);
  }
}

assertEnvironmentsAreValid();
