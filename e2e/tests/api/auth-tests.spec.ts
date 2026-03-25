import { test } from '../../fixtures/fixture';
import { debugLog } from '../../utils/debug-logging';
import { expect } from 'playwright/test';

test.describe('[MPT-15877] Authentication API Tests', { tag: '@auth' }, () => {
  test.describe.configure({ mode: 'parallel' });
  const email = process.env.DEFAULT_USER_EMAIL;
  const password = process.env.DEFAULT_USER_PASSWORD;
  const accountId = process.env.DEFAULT_ACCOUNT_ID;
  let accessToken: string;
  let refreshToken: string;

  test.afterEach(async () => {
    accessToken = '';
  });

  test('[231965] Get token for Operations API', { tag: '@p1' }, async ({ authRequest }) => {
    accessToken = await authRequest.getTokenForSpecificAccount(email, password, accountId);
    debugLog(`Access Token: ${accessToken}`);
    expect(accessToken).toBeTruthy();
  });

  test('[231966] Get token for last used account', async ({ authRequest }) => {
    accessToken = await authRequest.getTokenForLastUsedAccount(email, password);
    debugLog(`Access Token: ${accessToken}`);
    expect(accessToken).toBeTruthy();
  });

  test('[231967] Refresh token for Operations API', async ({ authRequest }) => {
    refreshToken = await authRequest.getRefreshToken(email, password, accountId);
    const newAccessToken = await authRequest.getAccessTokenWithRefreshToken(refreshToken, accountId);
    debugLog(`New Access Token: ${newAccessToken}`);
    expect(newAccessToken).toBeTruthy();
  });
});
