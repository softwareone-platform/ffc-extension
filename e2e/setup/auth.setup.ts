import { test as setup } from '@playwright/test';

import { Header, HomePage } from '../pages';
import TestUsers from '../test-data/test-users';
import { debugLog } from '../utils/debug-logging';
import { env, getCurrentEnv, requireEnv } from '../utils/env';
import { openPortalAndWaitForShell } from '../utils/test-steps';

const user = TestUsers.Admin;

// Serial: the second test signs in with the session the first one writes.
// Retried because a flaky IdP shouldn't fail the run on the first attempt.
setup.describe.configure({ mode: 'serial', retries: 1 });

setup('authenticate admin', async ({ browser }) => {
  requireEnv('defaultUserPassword');

  if (user.hasValidSession()) {
    debugLog(`Reusing cached session for ${user.email} (${env.baseUrl})`);
    return;
  }

  await setup.step(`Log in ${user.email}`, async () => {
    // Fatal on purpose: a swallowed login failure made every test fail obscurely.
    await user.login(browser);
  });
});

setup.describe('extension root', () => {
  setup.use({ storageState: user.sessionStoragePath });

  setup('cache extension root url', async ({ page }) => {
    setup.skip(user.extensionRootUrl !== undefined, 'Already stored alongside the reused session');

    const header = new Header(page);

    await openPortalAndWaitForShell(new HomePage(page), header);
    await header.openFinOpsForCloud();

    // The only menu click of the run: specs deep-link off the URL it redirects to, so
    // wait for the shell to settle rather than reading the pre-click URL.
    await page.waitForURL(new RegExp(`/extensions/${getCurrentEnv().extensionId}/`));
    user.saveExtensionRootUrl(page.url());
    debugLog(`Cached extension root URL ${page.url()} for ${user.email}`);
  });
});
