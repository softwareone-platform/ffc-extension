/** Where a run points its browser and API calls. */
type Deployment = {
  baseUrl: `https://${string}`;
  ffcClientBaseUrl: `https://${string}`;
};

/** Per-deployment identifiers the tests operate on. */
type EnvironmentFixtures = {
  extensionId: string;
  softwareOneOrgId: string;
  softwareOneOrgName: string;
  vendorAccountId: string;
  clientApiEmail: string;
  clientApiUserId: string;
  clientApiOrgId: string;
};

export type EnvironmentConfig = Deployment & EnvironmentFixtures;
