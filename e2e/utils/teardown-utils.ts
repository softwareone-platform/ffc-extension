import { FfcClientRequest } from '../api-request/ffc-client-request';
import { debugLog } from './debug-logging';
import { ERequestMethod } from '../types/enums';
import { getCurrentEnv } from './utils';
import { EmployeesResponse } from '../types/employees-response';

/**
 * Generates a headers object with a Bearer token for authorization.
 *
 * This function creates an object containing the `Content-Type` and `Authorization` headers.
 * The `Authorization` header includes a Bearer token for authenticated API requests.
 *
 * @param {string} token - The Bearer token to include in the `Authorization` header.
 * @returns {{ [key: string]: string }} An object containing the headers for an HTTP request.
 */
export function getBearerTokenHeader(token: string): { [key: string]: string } {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
}

/**
 * Deletes test users from the organisation when clean-up is enabled.
 *
 * Fetches all employees in the organisation configured via `DEFAULT_ORG_ID`,
 * identifies test users whose email starts with `mpt.qlt+ffc` and whose display
 * name is `Test User`, and deletes each one while reassigning their owned
 * resources to the user identified by `DEFAULT_USER_ID`.
 *
 * This function is a no-op when the `CLEAN_UP` environment variable is not set
 * to `'true'`, making it safe to call unconditionally at the end of a test run.
 *
 * @param {FfcClientRequest} request - The API request client used to call the FFC endpoints.
 * @param {string} token - A valid Bearer token for authenticating API requests.
 * @returns {Promise<void>} Resolves when all matching test users have been deleted,
 *   or immediately if clean-up is disabled.
 *
 * @remarks
 * - Relies on `BASE_URL` to derive the FFC API base URL by inserting `finops.`
 *   between `portal.` and `s1.` (e.g. `portal.s1.show` → `portal.finops.s1.show`).
 * - Only employees matching **both** the email prefix `mpt.qlt+ffc` **and** the
 *   display name `Test User` are deleted.
 * - Ownership is always reassigned to `DEFAULT_USER_ID` before deletion.
 */
export async function deleteTestUsers(request: FfcClientRequest, token: string): Promise<void> {
  if (process.env.CLEAN_UP !== 'true') {
    return;
  }
  const env = getCurrentEnv();
  const ffcClientBaseUrl = env.ffcClientBaseUrl;
  const reassignToUserId = env.clientAPI_userId;
  const organisationId = env.clientAPI_orgId;
  const usersEndpoint = `${ffcClientBaseUrl}/restapi/v2/organizations/${organisationId}/employees?exclude_myself=false&roles=true`;

  debugLog(`Fetching employees from endpoint: ${usersEndpoint}`);
  const headers = getBearerTokenHeader(token);

  const employeesResponse = await request.getResponse(usersEndpoint, ERequestMethod.GET, headers);
  const employeesResponseBody = (await employeesResponse.json()) as EmployeesResponse;

  for (const employee of employeesResponseBody.employees) {
    if (employee.user_email.startsWith('mpt.qlt+ffc-temp') && employee.user_display_name === 'Test User') {
      debugLog(`Deleting user: ${employee.user_email} with ID: ${employee.id}`);
      await request.deleteUserAndReassign(employee.id, reassignToUserId, token);
    }
  }
}
