import { APIResponse } from 'playwright-core';
import { request } from '@playwright/test';
import { PortalSettingsRequest } from '../requests/portal-settings-request';

/**
 * Accepts an invitation for a user by sending the required details to the server.
 *
 * @param {string} userId - The ID of the user accepting the invitation.
 * @param {string} token - The invitation token associated with the user.
 * @param {string} password - The password to set for the user.
 * @returns {Promise<APIResponse>} - A promise that resolves to the API response of the acceptance request.
 */
export async function acceptInvitation(userId: string, token: string, password: string): Promise<APIResponse> {
  const context = await request.newContext();
  const portalSettingsRequest = new PortalSettingsRequest(context);
  return await portalSettingsRequest.getUserAcceptInvitationResponse(userId, token, password);
}
