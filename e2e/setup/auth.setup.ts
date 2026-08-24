import { test as setup } from '@playwright/test';

import TestUsers from '../test-data/test-users';
import { debugLog } from '../utils/debug-logging';
import { env, requireEnv } from '../utils/env';

// A flaky IdP shouldn't fail the run on the first attempt.
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
    // Fatal on purpose: a swallowed login failure made every test fail obscurely.
    await user.login(browser);
  });
});
