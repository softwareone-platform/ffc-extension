import { deleteTestUsers } from '../utils/teardown-utils';
import { request } from '@playwright/test';
import { FfcClientRequest } from '../api-request/ffc-client-request';

async function globalTeardown() {
  if (process.env.CLEAN_UP === 'true') {
    const apiRequestContext = await request.newContext({
      ignoreHTTPSErrors: true,
      baseURL: process.env.BASE_URL,
    });
    const email = process.env.DEFAULT_USER_EMAIL;
    const password = process.env.DEFAULT_USER_PASSWORD;

    const ffcRequest = new FfcClientRequest(apiRequestContext);
    const token = await ffcRequest.getAuthorizationToken(email, password);

    await deleteTestUsers(ffcRequest, token);

    await apiRequestContext.dispose();
  }
}
module.exports = globalTeardown;
