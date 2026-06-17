import { TestData } from '../../types/TestData';
import { EEnvironment } from '../../types/enums';

export const devEnvironmentData: TestData = {
  name: EEnvironment.DEV,
  baseUrl: 'https://portal.s1.today',
  ffcClientBaseUrl: 'https://portal.finops.s1.today',
  admin_email: 'mpt.qlt+ffc-admin@gmail.com',
  default_userPassword: process.env.DEFAULT_USER_PASSWORD,
  extensionId: 'EXT-3055-0972',
  softwareOneOrgID: 'FORG-1317-5652-8045',
  vendorAccountId: 'ACC-2780-0539',
  clientAPI_email: 'finopstestuser@outlook.com',
  clientAPI_userId: 'da9c4030-dd0d-43ec-8a4f-108bab928db7',
  clientAPI_orgId: '3d0fe384-b1cf-4929-ad5e-1aa544f93dd5',
};