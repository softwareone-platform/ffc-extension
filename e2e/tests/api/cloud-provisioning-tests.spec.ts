import { test } from '../../fixtures/fixture';
import { generateRandomEmail, generateRandomOrganizationName } from '../../utils/random-data-generator';
import { getAccessToken } from '../../utils/getAccessToken';
import { expect } from 'playwright/test';
import { debugLog } from '../../utils/debug-logging';
import { v4 as uuidv4 } from 'uuid';
import { getNewEmployeeID } from '../../utils/getNewEmployeeID';
import { GetEmployeesByOrganisationIDResponse } from '../../types/get-employees-by-organization-id';
import { deleteOrganization } from '../../utils/delete-organization';
import { GetOrganizationByIDResponse } from '../../types/get-organizations-by-id-response';
import { GetDatasourcesByOrganizationIDResponse } from '../../types/get-datasources-by-organization-id';
import { isDatasourceType } from '../../utils/is-valid-type';

let createEmployeeData: {
  display_name: string;
  email: string;
};

let createOrgData: {
  name: string;
  currency: string;
  billing_currency: string;
  operations_external_id: string;
  user_id: string;
};

async function setNewEmployeeData() {
  createEmployeeData = {
    display_name: `Test Employee ${Date.now()}`,
    email: generateRandomEmail(),
  };
}

async function setNewOrganizationData(headers: { [key: string]: string }) {
  createOrgData = {
    name: generateRandomOrganizationName(),
    currency: 'EUR',
    billing_currency: 'EUR',
    operations_external_id: uuidv4(),
    user_id: await getNewEmployeeID(headers),
  };
}

test.describe('[MPT-15877] Cloud Provisioning tests', { tag: '@cloud-provisioning' }, () => {
  test.describe.configure({ mode: 'parallel' });
  let headers: { [key: string]: string };
  let organizationID: string;

  test.beforeAll(async () => {
    headers = {
      Authorization: `Bearer ${await getAccessToken()}`,
      'Content-Type': 'application/json',
    };
  });

  test.afterEach(async () => {
    createEmployeeData = null;
    if (organizationID) {
      await deleteOrganization(headers, organizationID);
      organizationID = '';
      createOrgData = null;
    }
  });

  test('[231971] Create a new employee', { tag: '@p1' }, async ({ cloudProvisioningRequest }) => {
    await setNewEmployeeData();
    const response = await cloudProvisioningRequest.createEmployee(headers, createEmployeeData);
    const { email, display_name, roles_count, id } = await response.json();

    debugLog(`Created Employee ID: ${id}`);

    expect(response.status()).toBe(201);
    expect(display_name).toBe(createEmployeeData.display_name);
    expect(id).toBeTruthy();
    expect(email).toBe(createEmployeeData.email);
    expect(roles_count).toBeFalsy();
  });

  test('[231972] Create Organization', { tag: '@p1' }, async ({ cloudProvisioningRequest }) => {
    await setNewOrganizationData(headers);
    const response = await cloudProvisioningRequest.createOrganization(headers, createOrgData);
    const { id } = await response.json();
    debugLog(`Created Organization ID: ${id}`);
    organizationID = id;

    expect(response.status()).toBe(201);
    expect(id).toMatch(/^FORG-\d{4}-\d{4}-\d{4}$/);
  });

  test('[231973] Update Organization', { tag: '@p1' }, async ({ cloudProvisioningRequest }) => {
    await setNewOrganizationData(headers);
    organizationID = await cloudProvisioningRequest.getNewOrganizationID(headers, createOrgData);
    const updateData = {
      name: generateRandomOrganizationName(),
      operations_external_id: uuidv4(),
    };
    const response = await cloudProvisioningRequest.updateOrganization(headers, organizationID, updateData);
    const { name, operations_external_id } = await response.json();

    expect(response.status()).toBe(200);
    expect(name).toBe(updateData.name);
    expect(operations_external_id).toBe(updateData.operations_external_id);
  });

  test('[231974] Delete Organization by ID', { tag: '@p1' }, async ({ cloudProvisioningRequest }) => {
    await setNewOrganizationData(headers);
    organizationID = await cloudProvisioningRequest.getNewOrganizationID(headers, createOrgData);
    const response = await cloudProvisioningRequest.deleteOrganization(headers, organizationID);

    expect(response.status()).toBe(204);
    organizationID = '';
  });

  test('[231975] Get Employees by Organization ID', { tag: '@p1' }, async ({ cloudProvisioningRequest }) => {
    await setNewEmployeeData();
    const employeeId = await cloudProvisioningRequest.getCreateEmployeeID(headers, createEmployeeData);
    debugLog(`Created Employee ID: ${employeeId}`);

    const orgData = {
      name: generateRandomOrganizationName(),
      currency: 'EUR',
      billing_currency: 'EUR',
      operations_external_id: uuidv4(),
      user_id: employeeId,
    };

    organizationID = await cloudProvisioningRequest.getNewOrganizationID(headers, orgData);
    const orgResponse = await cloudProvisioningRequest.getEmployeesByOrganizationId(headers, organizationID);
    const body = (await orgResponse.json()) as GetEmployeesByOrganisationIDResponse;

    expect(orgResponse.status()).toBe(200);
    expect.soft(body.length).toBe(1);
    expect.soft(body[0].email).toBe(createEmployeeData.email);
    expect.soft(body[0].display_name).toBe(createEmployeeData.display_name);
  });

  test('[231976] Get Employee by email', { tag: '@p1' }, async ({ cloudProvisioningRequest }) => {
    await setNewEmployeeData();
    await cloudProvisioningRequest.createEmployee(headers, createEmployeeData);

    const response = await cloudProvisioningRequest.getEmployeeByEmail(headers, createEmployeeData.email);
    const body = await response.json();

    expect(response.status()).toBe(200);
    expect(body.email).toBe(createEmployeeData.email);
    expect(body.display_name).toBe(createEmployeeData.display_name);
  });

  test('[231977] Get all organizations', async ({ cloudProvisioningRequest }) => {
    const response = await cloudProvisioningRequest.getOrganizations(headers, 600);
    const organizations = await response.json();

    debugLog(`Organizations Response: ${JSON.stringify(organizations)}`);

    expect(response.status()).toBe(200);
  });

  test('[231978] Get organization by ID', async ({ cloudProvisioningRequest }) => {
    const id = process.env.OPS_ORG_ID;
    const response = await cloudProvisioningRequest.getOrganizationById(headers, id);
    const body = (await response.json()) as GetOrganizationByIDResponse;

    expect(response.status()).toBe(200);
    expect(body.id).toBe(id);
    expect(body.name).toBe('SoftwareOne (Test Environment)');
  });

  test('[231983] Get data sources', { tag: '@p1' }, async ({ cloudProvisioningRequest }) => {
    const id = process.env.OPS_ORG_ID;
    const response = await cloudProvisioningRequest.getDataSources(headers, id);
    const body = (await response.json()) as GetDatasourcesByOrganizationIDResponse;

    debugLog(`Data Sources Response: ${JSON.stringify(body)}`);
    for (const ds of body) {
      expect(ds.id).toBeTruthy();
      expect(ds.name).toBeTruthy();
      expect(isDatasourceType(ds.type)).toBe(true);
      expect(ds.resources_charged_this_month).toBeGreaterThanOrEqual(0);
      expect(ds.expenses_so_far_this_month).toBeGreaterThanOrEqual(0);
      expect(ds.expenses_forecast_this_month).toBeGreaterThanOrEqual(0);
    }

    expect(response.status()).toBe(200);
  });

  test('[232040] Force reimport of data sources', { tag: '@p1' }, async ({ cloudProvisioningRequest }) => {
    const orgId = process.env.OPS_ORG_ID;
    const dsId = await cloudProvisioningRequest.getDataSourceByName(headers, orgId, 'Marketplace (Dev)');
    const response = await cloudProvisioningRequest.getForceReimportDataSource(headers, orgId, dsId);

    debugLog(`Force Reimport Response Status: ${response.status()}`);
    expect(response.status()).toBe(204);
  });

  test('[232041] Add a new user as organization admin', { tag: '@p1' }, async ({ cloudProvisioningRequest }) => {
    await test.step('Create Organization', async () => {
      await setNewOrganizationData(headers);
      organizationID = await cloudProvisioningRequest.getNewOrganizationID(headers, createOrgData);
    });

    const email = generateRandomEmail();
    const displayName = `Org Admin ${Date.now()}`;

    await test.step('Add Additional Admin to Organization', async () => {
      const response = await cloudProvisioningRequest.getAddAdditionalAdminResponse(headers, organizationID, email, displayName);

      debugLog(`Add Additional Admin Response Status: ${response.status()}`);
      expect(response.status()).toBe(200);
    });

    await test.step('Verify New Admin in Organization Employees', async () => {
      const organizationResponse = await cloudProvisioningRequest.getEmployeesByOrganizationId(headers, organizationID);
      const body = (await organizationResponse.json()) as GetEmployeesByOrganisationIDResponse;

      debugLog(`Organization Details Response body: ${JSON.stringify(body)}`);

      expect(body.length).toBe(2);
      const newAdmin = body.find(emp => emp.email === email);
      expect(newAdmin).toBeDefined();
      expect(newAdmin.display_name).toBe(displayName);
    });
  });
});
