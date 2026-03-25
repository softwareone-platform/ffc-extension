import { request } from '@playwright/test';
import { PortalSettingsRequest } from '../requests/portal-settings-request';
import { generateRandomEmail } from './random-data-generator';
import { acceptInvitation } from './accept-invitation';

/**
 * Asynchronously creates a new invited user and returns the user ID.
 *
 * @param {Object} headers - An object containing the headers for the request.
 * @param {string} [accountId=''] - The account ID to associate with the user. Defaults to an environment variable if not provided.
 * @param {string} [email=''] - The email address of the user. A random email is generated if not provided.
 * @param {string} [password=''] - The password for the user. Defaults to an environment variable if not provided.
 * @returns {Promise<string>} - A promise that resolves to the ID of the newly invited user.
 */
export async function getNewInvitedUser(
  headers: { [key: string]: string },
  accountId: string = '',
  email: string = '',
  password: string = ''
): Promise<string> {
  const context = await request.newContext();
  const portalSettingsResponse = new PortalSettingsRequest(context);
  email ||= generateRandomEmail();
  password ||= process.env.DEFAULT_USER_PASSWORD;
  accountId ||= process.env.DEFAULT_ACCOUNT_ID;
  const userName = 'Test User';

  const inviteResponse = await portalSettingsResponse.getInviteUserResponse(headers, userName, email, accountId);
  const token = await portalSettingsResponse.getInvitationToken(inviteResponse);
  const userId = await portalSettingsResponse.getInvitedUserID(inviteResponse);
  await acceptInvitation(userId, token, password);
  return userId;
}
