import {EEnvironment} from "./enums";

export interface TestData {
  name: EEnvironment;
  baseUrl: string;
  ffcClientBaseUrl: string;
  default_userPassword: string | undefined;
  extensionId: string;
  softwareOneOrgID: string;
  vendorAccountId?: string;
  clientAPI_email: string;
  clientAPI_userId: string;
  clientAPI_orgId: string;
}
