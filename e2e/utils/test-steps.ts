import { test } from '@playwright/test';

import { Header, HomePage } from '../pages';

export async function openPortalAndWaitForShell(homePage: HomePage, header: Header): Promise<void> {
  await test.step('Open portal and wait for shell', async () => {
    await homePage.navigateToURL();
    await homePage.waitForIframeLoading();
    await header.tenantName.waitFor();
  });
}
