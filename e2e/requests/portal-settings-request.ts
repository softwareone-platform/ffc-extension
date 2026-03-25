import { APIRequestContext, APIResponse } from 'playwright-core';
import { OpsBaseRequest } from './ops-base-request';
import { ERequestMethod } from '../types/enums';
import { InviteUserResponse } from '../types/invite-user-response';

export class PortalSettingsRequest extends OpsBaseRequest {
  readonly request: APIRequestContext;
  readonly usersEndpoint: string;
  readonly systemsEndpoint: string;

  constructor(request: APIRequestContext) {
    super(request);
    this.request = request;
    this.usersEndpoint = `${this.opsUrl}/users`;
    this.systemsEndpoint = `${this.opsUrl}/systems`;
  }

  /**
   * Sends a request to invite a user to the system.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {string} name - The name of the user to invite.
   * @param {string} email - The email address of the user to invite.
   * @param {string} accountId - The account ID associated with the user.
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response.
   * @throws {Error} - Throws an error if the response status is not 201.
   */
  async getInviteUserResponse(headers: { [key: string]: string }, name: string, email: string, accountId: string): Promise<APIResponse> {
    const data = {
      name: name,
      email: email,
      account: {
        id: accountId,
      },
    };
    const response = await this.getResponse(this.usersEndpoint, ERequestMethod.POST, headers, data);
    if (response.status() !== 201) {
      throw new Error(`Failed to invite user, status code: ${response.status()}`);
    }
    return response;
  }

  /**
   * Extracts the invitation token from the API response.
   *
   * @param {APIResponse} response - The API response containing the invitation token.
   * @returns {Promise<string>} - A promise that resolves to the invitation token.
   */
  async getInvitationToken(response: APIResponse): Promise<string> {
    const responseBody = (await response.json()) as InviteUserResponse;

    return responseBody.account_user.invitation_token;
  }

  /**
   * Retrieves the ID of the invited user from the API response.
   *
   * @param {APIResponse} response - The API response containing the invited user's details.
   * @returns {Promise<string>} - A promise that resolves to the ID of the invited user.
   */
  async getInvitedUserID(response: APIResponse): Promise<string> {
    const responseBody = (await response.json()) as InviteUserResponse;

    return responseBody.id;
  }

  /**
   * Sends a request to accept a user invitation.
   *
   * @param {string} userId - The ID of the user accepting the invitation.
   * @param {string} token - The invitation token for the user.
   * @param {string} password - The password to set for the user.
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response.
   * @throws {Error} - Throws an error if the response status is not 200.
   */
  async getUserAcceptInvitationResponse(userId: string, token: string, password: string): Promise<APIResponse> {
    const endpoint = `${this.usersEndpoint}/${userId}/accept-invitation`;
    const headers = {
      accept: 'application/json',
      'Content-Type': 'application/json',
    };
    const data = {
      password: password,
      invitation_token: token,
    };
    const response = await this.getResponse(endpoint, ERequestMethod.POST, headers, data);
    if (response.status() !== 200) {
      throw new Error('Failed to accept user invitation');
    }
    return response;
  }
}
