import { EnvironmentConfig } from './types/environment';

export const ENVIRONMENTS = {
  TEST: {
    baseUrl: 'https://portal.s1.show',
    ffcClientBaseUrl: 'https://portal.finops.s1.show',
    extensionId: 'EXT-3438-0205',
    softwareOneOrgId: 'FORG-1317-5652-8045',
    vendorAccountId: 'ACC-3805-2089',
    clientApiEmail: 'finopstestuser@outlook.com',
    clientApiUserId: '85dfff1d-6f5f-4271-9d1e-e7e911f39728',
    clientApiOrgId: '4eae08f8-9b40-4094-a11c-f9ee2dc76a12',
  },
  DEV: {
    baseUrl: 'https://portal.s1.today',
    ffcClientBaseUrl: 'https://portal.finops.s1.today',
    extensionId: 'EXT-3055-0972',
    softwareOneOrgId: 'FORG-1317-5652-8045',
    vendorAccountId: 'ACC-2780-0539',
    clientApiEmail: 'finopstestuser@outlook.com',
    clientApiUserId: 'da9c4030-dd0d-43ec-8a4f-108bab928db7',
    clientApiOrgId: '3d0fe384-b1cf-4929-ad5e-1aa544f93dd5',
  },
} as const satisfies Record<string, EnvironmentConfig>;

export type EnvironmentKey = keyof typeof ENVIRONMENTS;

export const ENVIRONMENT_KEYS = Object.keys(ENVIRONMENTS) as EnvironmentKey[];

const BARE_ORIGIN_PATTERN = /^https:\/\/[a-z0-9]([a-z0-9.-]*[a-z0-9])?(?::\d{1,5})?$/i;

export const isBareOrigin = (value: string): boolean => BARE_ORIGIN_PATTERN.test(value);

// Import-time: a bad definition fails before the first test.
function assertEnvironmentsAreValid(): void {
  const problems: string[] = [];

  for (const key of ENVIRONMENT_KEYS) {
    for (const field of ['baseUrl', 'ffcClientBaseUrl'] as const) {
      const url = ENVIRONMENTS[key][field];
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
