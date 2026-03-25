import { request } from '@playwright/test';
import { CloudProvisioningRequest } from '../requests/cloudProvisioningRequest';
import { debugLog } from './debug-logging';

export async function deleteOrganization(headers: { [key: string]: string }, organizationId: string): Promise<void> {
  const context = await request.newContext();
  const cloudProvisioningRequest = new CloudProvisioningRequest(context);

  await cloudProvisioningRequest.deleteOrganization(headers, organizationId);
  debugLog(`Deleted Organization ID: ${organizationId}`);
}
