import { request } from '@playwright/test';

import { FfcClientRequest } from '../api-request/ffc-client-request';
import { env, getCurrentEnv, requireEnv } from '../utils/env';
import { deleteTestUsers } from '../utils/teardown-utils';

async function globalTeardown() {
  if (env.cleanUp) {
    // Fail naming the var rather than sending an empty password.
    requireEnv('defaultUserPassword');

    const testData = getCurrentEnv();

    const apiRequestContext = await request.newContext({
      ignoreHTTPSErrors: env.ignoreHttpsErrors,
      baseURL: testData.baseUrl,
    });

    const ffcRequest = new FfcClientRequest(apiRequestContext);
    const token = await ffcRequest.getAuthorizationToken(testData.clientApiEmail, env.defaultUserPassword);

    await deleteTestUsers(ffcRequest, token);

    await apiRequestContext.dispose();
  }
}
module.exports = globalTeardown;
