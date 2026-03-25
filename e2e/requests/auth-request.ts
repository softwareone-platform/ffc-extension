import { OpsBaseRequest } from './ops-base-request';
import { APIRequestContext } from 'playwright-core';
import { ERequestMethod } from '../types/enums';
import { debugLog } from '../utils/debug-logging';

export class AuthRequest extends OpsBaseRequest {
  readonly request: APIRequestContext;
  readonly tokensEndpoint: string;
  readonly passwordRecoveryEndpoint: string;

  private headers = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  };

  /**=
   * Constructs an instance of AuthRequest.
   * @param {APIRequestContext} request - The API request context.
   */
  constructor(request: APIRequestContext) {
    super(request);
    this.request = request;
    this.tokensEndpoint = `${this.opsUrl}/auth/tokens`;
    this.passwordRecoveryEndpoint = `${this.opsUrl}/auth/password-recovery-requests/`;
  }

  /**
   * Retrieves an access token for the last used account based on the provided email and password.
   *
   * @param {string} email - The email address of the user.
   * @param {string} password - The password of the user.
   * @returns {Promise<string>} - A promise that resolves to the access token.
   * @throws {Error} - Throws an error if the token generation fails.
   */
  async getTokenForLastUsedAccount(email: string, password: string): Promise<string> {
    const data = {
      email: email,
      password: password,
    };
    const response = await this.getResponse(this.tokensEndpoint, ERequestMethod.POST, this.headers, data);
    if (response.status() !== 200) {
      throw new Error('Failed to generate token');
    }
    const { access_token } = await response.json();
    debugLog(`Token: ${access_token}`);
    return access_token;
  }

  /**
   * Retrieves an access token for a specific account based on the provided email, password, and account ID.
   *
   * @param {string} email - The email address of the user.
   * @param {string} password - The password of the user.
   * @param {string} accountId - The ID of the specific account.
   * @returns {Promise<string>} - A promise that resolves to the access token.
   * @throws {Error} - Throws an error if the token generation fails.
   */
  async getTokenForSpecificAccount(email: string, password: string, accountId: string): Promise<string> {
    const data = {
      email: email,
      password: password,
      account: {
        id: accountId,
      },
    };
    const response = await this.getResponse(this.tokensEndpoint, ERequestMethod.POST, this.headers, data);
    if (response.status() !== 200) {
      throw new Error('Failed to generate token');
    }
    const { access_token } = await response.json();
    debugLog(`Token: ${access_token}`);
    return access_token;
  }

  /**
   * Retrieves a refresh token for a specific account based on the provided email, password, and account ID.
   *
   * @param {string} email - The email address of the user.
   * @param {string} password - The password of the user.
   * @param {string} accountId - The ID of the specific account.
   * @returns {Promise<string>} - A promise that resolves to the refresh token.
   * @throws {Error} - Throws an error if the token generation fails.
   */
  async getRefreshToken(email: string, password: string, accountId: string): Promise<string> {
    const data = {
      email: email,
      password: password,
      account: {
        id: accountId,
      },
    };
    const response = await this.getResponse(this.tokensEndpoint, ERequestMethod.POST, this.headers, data);
    if (response.status() !== 200) {
      throw new Error('Failed to generate token');
    }
    const { refresh_token } = await response.json();
    debugLog(`Refresh Token: ${refresh_token}`);
    return refresh_token;
  }

  /**
   * Retrieves an access token using a refresh token and account ID.
   *
   * @param {string} refreshToken - The refresh token to generate a new access token.
   * @param {string} accountId - The ID of the specific account.
   * @returns {Promise<string>} - A promise that resolves to the access token.
   * @throws {Error} - Throws an error if the token generation fails.
   */
  async getAccessTokenWithRefreshToken(refreshToken: string, accountId: string): Promise<string> {
    const data = {
      refresh_token: refreshToken,
      account: {
        id: accountId,
      },
    };
    const response = await this.getResponse(this.tokensEndpoint, ERequestMethod.POST, this.headers, data);
    if (response.status() !== 200) {
      throw new Error(`Failed to generate access token with refresh token: Status ${response.status()}`);
    }
    const { access_token } = await response.json();
    debugLog(`Access Token: ${access_token}`);
    return access_token;
  }
}
