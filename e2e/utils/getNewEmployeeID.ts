import { request } from '@playwright/test';
import { CloudProvisioningRequest } from '../requests/cloudProvisioningRequest';
import { generateRandomEmail } from './random-data-generator';

export async function getNewEmployeeID(headers: { [key: string]: string }): Promise<string> {
  const context = await request.newContext();
  const cloudProvisioningRequest = new CloudProvisioningRequest(context);

  const data = {
    display_name: `Test Employee ${Date.now()}`,
    email: generateRandomEmail(),
  };

  return await cloudProvisioningRequest.getCreateEmployeeID(headers, data);
}
