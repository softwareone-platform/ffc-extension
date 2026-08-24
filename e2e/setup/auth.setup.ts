import { test as setup } from '@playwright/test';

import TestUsers from '../test-data/test-users';
import { debugLog } from '../utils/debug-logging';
import { env, requireEnv } from '../utils/env';

// A flaky identity provider shouldn't fail the whole run on the first attempt.
setup.describe.configure({ retries: 1 });

setup('authenticate admin', async ({ browser }) => {
  requireEnv('defaultUserPassword');

  const user = TestUsers.Admin;

  const reusable = await setup.step('Check cached session', () => user.hasValidSession(browser));
  if (reusable) {
    debugLog(`Reusing cached session for ${user.email} (${env.testEnv})`);
    return;
  }

  await setup.step(`Log in ${user.email}`, async () => {
    // Failing here is fatal on purpose: previously a failed login was swallowed
    // and every test then failed for an unrelated-looking reason.
    await user.login(browser);
  });
});
