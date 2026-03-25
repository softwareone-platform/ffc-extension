import { test } from '../../fixtures/fixture';
import { getAccessToken } from '../../utils/getAccessToken';
import { generateRandomEmail } from '../../utils/random-data-generator';
import { debugLog } from '../../utils/debug-logging';
import { expect } from 'playwright/test';
import { AcceptUserInvitationResponse } from '../../types/accept-user-invitation-response';

test.describe('[MPT-15877] Portal Settings tests', { tag: '@portal-settings' }, () => {
  test.describe.configure({ mode: 'parallel' });

  let headers: { [key: string]: string };

  test.beforeAll(async () => {
    headers = {
      Authorization: `Bearer ${await getAccessToken()}`,
      'Content-Type': 'application/json',
    };
  });

  test('[232043] Invite User and accept invitation', { tag: '@p1' }, async ({ portalSettingsRequest }) => {
    const accountId = process.env.DEFAULT_ACCOUNT_ID;
    const userName = 'Test User';
    const userEmail = generateRandomEmail();
    const password = process.env.DEFAULT_USER_PASSWORD;

    const inviteResponse = await portalSettingsRequest.getInviteUserResponse(headers, userName, userEmail, accountId);

    const token = await portalSettingsRequest.getInvitationToken(inviteResponse);
    debugLog(`Invitation token: ${token}`);
    const userId = await portalSettingsRequest.getInvitedUserID(inviteResponse);
    debugLog(`Invited user ID: ${userId}`);

    const response = await portalSettingsRequest.getUserAcceptInvitationResponse(userId, token, password);
    const body = (await response.json()) as AcceptUserInvitationResponse;
    debugLog(`Accept Invitation Response Body: ${JSON.stringify(body)}`);

    expect(response.status()).toBe(200);
    expect(body.status).toBe('active');
  });
});
