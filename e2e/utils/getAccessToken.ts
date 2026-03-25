import { AuthRequest } from '../requests/auth-request';
import { request } from '@playwright/test';

export async function getAccessToken(email = '', password = '', accountId = ''): Promise<string> {
  const context = await request.newContext();
  const authRequest = new AuthRequest(context);
  email ||= process.env.DEFAULT_USER_EMAIL;
  password ||= process.env.DEFAULT_USER_PASSWORD;
  accountId ||= process.env.DEFAULT_ACCOUNT_ID;

  return await authRequest.getTokenForSpecificAccount(email, password, accountId);
}
