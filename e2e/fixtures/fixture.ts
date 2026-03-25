import { test as base } from '@playwright/test';
import { AuthRequest } from '../requests/auth-request';
import { CloudProvisioningRequest } from '../requests/cloudProvisioningRequest';
import { PortalSettingsRequest } from '../requests/portal-settings-request';

/**
 * Extends the base test with custom fixtures for API requests.
 */
export const test = base.extend<{
  authRequest: AuthRequest;
  cloudProvisioningRequest: CloudProvisioningRequest;
  portalSettingsRequest: PortalSettingsRequest;
}>({
  authRequest: async ({ request }, use) => {
    await use(new AuthRequest(request));
  },
  cloudProvisioningRequest: async ({ request }, use) => {
    await use(new CloudProvisioningRequest(request));
  },
  portalSettingsRequest: async ({ request }, use) => {
    await use(new PortalSettingsRequest(request));
  },
});
