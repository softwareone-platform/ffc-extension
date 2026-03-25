import { APIRequestContext, APIResponse } from 'playwright-core';
import { ERequestMethod } from '../types/enums';

/**
 * Abstract base class for making HTTP requests to the Ops API.
 */
export abstract class OpsBaseRequest {
  /** The API request context provided by Playwright. */
  readonly request: APIRequestContext;

  /** The base URL for the Ops API. */
  readonly opsUrl: string;

  /**
   * Constructs an instance of OpsBaseRequest.
   *
   * @param {APIRequestContext} request - The API request context used to make HTTP requests.
   */
  protected constructor(request: APIRequestContext) {
    this.opsUrl = `${process.env.BASE_URL}/ops/v1`;
    this.request = request;
  }

  /**
   * Sends an HTTP request to the specified endpoint using the given method, headers, and optional data.
   *
   * @param {string} endpoint - The API endpoint to send the request to.
   * @param {ERequestMethod} method - The HTTP method to use (e.g., GET, POST, etc.).
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {unknown} [data] - Optional data to include in the request body (for POST, PUT, or PATCH methods).
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response.
   * @throws {Error} - Throws an error if the HTTP method is unsupported.
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
    return response;
  }
}
