import { TestData } from '../../types/TestData';
import { EEnvironment } from '../../types/enums';

export const testEnvironmentData: TestData = {
  name: EEnvironment.TEST,
  baseUrl: 'https://portal.s1.show',
  ffcClientBaseUrl: 'https://portal.finops.s1.show',
  default_userPassword: process.env.DEFAULT_USER_PASSWORD,

  extensionId: 'EXT-3438-0205',
  softwareOneOrgID: 'FORG-1317-5652-8045',
  vendorAccountId: 'ACC-3805-2089',
  clientAPI_email: 'finopstestuser@outlook.com',
  clientAPI_orgId: '4eae08f8-9b40-4094-a11c-f9ee2dc76a12',
  clientAPI_userId: '85dfff1d-6f5f-4271-9d1e-e7e911f39728',
};