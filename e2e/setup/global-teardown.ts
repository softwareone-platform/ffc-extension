import { deleteTestUsers } from '../utils/teardown-utils';
import { request } from '@playwright/test';
import { FfcClientRequest } from '../api-request/ffc-client-request';
import { getCurrentEnv } from '../utils/utils';

async function globalTeardown() {
  if (process.env.CLEAN_UP === 'true') {
    const env = getCurrentEnv();
    const password = process.env.DEFAULT_USER_PASSWORD;

    const apiRequestContext = await request.newContext({
      ignoreHTTPSErrors: true,
      baseURL: env.baseUrl,
    });

    const email = env.clientAPI_email;

    const ffcRequest = new FfcClientRequest(apiRequestContext);
    const token = await ffcRequest.getAuthorizationToken(email, password);

    await deleteTestUsers(ffcRequest, token);

    await apiRequestContext.dispose();
  }
}
module.exports = globalTeardown;
