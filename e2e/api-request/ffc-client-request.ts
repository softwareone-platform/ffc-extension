import { type APIRequestContext, APIResponse } from '@playwright/test';
import { ERequestMethod } from '../types/enums';
import { debugLog } from '../utils/debug-logging';
import { getBearerTokenHeader } from '../utils/teardown-utils';
import { getCurrentEnv } from '../utils/utils';

export class FfcClientRequest {
  readonly request: APIRequestContext;
  readonly userEndpoint: string;
  readonly tokenEndpoint: string;
  readonly employeesEndpoint: string;

  public constructor(request: APIRequestContext) {
    this.request = request;
    const ffcClientBaseUrl = getCurrentEnv().ffcClientBaseUrl;
    this.userEndpoint = `${ffcClientBaseUrl}/auth/v2/users`;
    this.tokenEndpoint = `${ffcClientBaseUrl}/auth/v2/tokens`;
    this.employeesEndpoint = `${ffcClientBaseUrl}/restapi/v2/employees`;
  }

  /**
   * Sends an HTTP request to the specified endpoint using the given method, headers, and optional data.
   *
   * @param {string} endpoint - The API endpoint to send the request to.
   * @param {ERequestMethod} method - The HTTP method to use (e.g., GET, POST, etc.).
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {unknown} [data] - Optional data to include in the request body (for POST, PUT, or PATCH methods).
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response.
   * @throws {Error} - Throws an error if the HTTP method is unsupported or the response status is not a success code (2xx).
   */
  async getResponse(
    endpoint: string,
    method: ERequestMethod,
    headers: {
      [key: string]: string;
    },
    data?: unknown
  ): Promise<APIResponse> {
    let response: APIResponse;
    switch (method) {
      case ERequestMethod.GET:
        response = await this.request.get(endpoint, { headers });
        break;
      case ERequestMethod.POST:
        response = await this.request.post(endpoint, { headers, data });
        break;
      case ERequestMethod.PUT:
        response = await this.request.put(endpoint, { headers, data });
        break;
      case ERequestMethod.DELETE:
        response = await this.request.delete(endpoint, { headers });
        break;
      case ERequestMethod.PATCH:
        response = await this.request.patch(endpoint, { headers, data });
        break;
      default:
        throw new Error(`Unsupported request method: ${method}`);
    }

    if (!response.ok()) {
      const statusCode = response.status();
      throw new Error(
        `HTTP request failed with status ${statusCode}: ${response.statusText()} ` + `(method: ${method}, endpoint: ${endpoint})`
      );
    }

    return response;
  }

  /**
   * Authorizes a user with the provided email and password.
   * @param {string} email - The email address of the user.
   * @param {string} password - The password of the user.
   * @returns {Promise<APIResponse>} A promise that resolves to the API response.
   */
  async authorization(email: string, password: string): Promise<APIResponse> {
    return await this.request.post(this.tokenEndpoint, {
      headers: {
        'Content-Type': 'application/json',
      },
      data: {
        email: email,
        password: password,
      },
    });
  }
  /**
   * Gets an authorization token for the provided email and password.
   * @param {string} email - The email address of the user.
   * @param {string} password - The password of the user.
   * @returns {Promise<string>} A promise that resolves to the authorization token.
   * @throws Will throw an error if the token generation fails.
   */
  async getAuthorizationToken(email: string, password: string): Promise<string> {
    const response = await this.authorization(email, password);
    if (response.status() !== 201) {
      throw new Error('Failed to generate token');
    }
    const { token } = await response.json();
    debugLog(`Token: ${token}`);
    return token;
  }

  /**
   * Deletes a user and reassigns their ownership to another user.
   *
   * @param {string} userID - The ID of the user to delete.
   * @param {string} reassignUserID - The ID of the user to whom ownership will be reassigned.
   * @param {string} token - The authorization token for the API request.
   * @returns {Promise<string>} A promise that resolves to a confirmation message upon successful deletion.
   * @throws Will throw an error if the deletion fails (non-204 response status).
   */
  async deleteUserAndReassign(userID: string, reassignUserID: string, token: string): Promise<string> {
    const endpoint = `${this.employeesEndpoint}/${userID}?new_owner_id=${reassignUserID}`;
    debugLog(`Deleting user ${userID} and reassigning to ${reassignUserID}`);
    const response = await this.request.delete(endpoint, {
      headers: getBearerTokenHeader(token),
      data: {
        new_owner_id: reassignUserID,
      },
    });
    if (response.status() !== 204) {
      throw new Error(`[ERROR] Failed to delete userID: ${userID}`);
    }
    return `User ${userID} deleted`;
  }
}
