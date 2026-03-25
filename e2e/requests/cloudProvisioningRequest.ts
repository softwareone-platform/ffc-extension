import { OpsBaseRequest } from './ops-base-request';
import { APIRequestContext, APIResponse } from 'playwright-core';
import { ERequestMethod } from '../types/enums';
import { debugLog } from '../utils/debug-logging';
import { GetDatasourcesByOrganizationIDResponse } from '../types/get-datasources-by-organization-id';

export class CloudProvisioningRequest extends OpsBaseRequest {
  readonly request: APIRequestContext;
  readonly organizationsEndpoint: string;
  readonly employeesEndpoint: string;

  constructor(request: APIRequestContext) {
    super(request);
    this.request = request;
    this.organizationsEndpoint = `${this.opsUrl}/organizations`;
    this.employeesEndpoint = `${this.opsUrl}/employees`;
  }

  /**
   * Creates a new employee by sending a POST request to employees endpoint.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {unknown} data - The data to include in the request body.
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response.
   */
  async createEmployee(headers: { [key: string]: string }, data: unknown): Promise<APIResponse> {
    return await this.getResponse(this.employeesEndpoint, ERequestMethod.POST, headers, data);
  }

  /**
   * Creates a new employee and retrieves their ID.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {unknown} data - The data to include in the request body.
   * @returns {Promise<string>} - A promise that resolves to the employee ID.
   * @throws {Error} - Throws an error if the employee creation fails.
   */
  async getCreateEmployeeID(headers: { [key: string]: string }, data: unknown): Promise<string> {
    const response = await this.createEmployee(headers, data);
    if (response.status() !== 201) {
      throw new Error('Failed to create employee');
    }
    const { id } = await response.json();
    return id;
  }

  /**
   * Retrieves a list of employees for a specific organization.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {string} organizationId - The ID of the organization whose employees are to be retrieved.
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response containing the employees.
   */
  async getEmployeesByOrganizationId(headers: { [key: string]: string }, organizationId: string): Promise<APIResponse> {
    const endpoint = `${this.organizationsEndpoint}/${organizationId}/employees`;
    return await this.getResponse(endpoint, ERequestMethod.GET, headers);
  }

  /**
   * Retrieves an employee's details by their email address.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {string} email - The email address of the employee to retrieve.
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response containing the employee's details.
   */
  async getEmployeeByEmail(headers: { [key: string]: string }, email: string): Promise<APIResponse> {
    const endpoint = `${this.employeesEndpoint}/${encodeURIComponent(email)}`;
    return await this.getResponse(endpoint, ERequestMethod.GET, headers);
  }

  /**
   * Retrieves a list of organizations with optional pagination.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {number} [limit=50] - The maximum number of organizations to retrieve.
   * @param {number} [offset=0] - The offset for pagination.
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response.
   */
  async getOrganizations(headers: { [key: string]: string }, limit: number = 50, offset: number = 0): Promise<APIResponse> {
    const endpointWithParams = `${this.organizationsEndpoint}?limit=${limit}&offset=${offset}`;
    return await this.getResponse(endpointWithParams, ERequestMethod.GET, headers);
  }

  /**
   * Retrieves the details of an organization by its ID.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {string} organizationId - The ID of the organization to retrieve.
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response containing the organization's details.
   */
  async getOrganizationById(headers: { [key: string]: string }, organizationId: string): Promise<APIResponse> {
    const endpoint = `${this.organizationsEndpoint}/${organizationId}`;
    return await this.getResponse(endpoint, ERequestMethod.GET, headers);
  }

  /**
   * Creates a new organization by sending a POST request to the organization's endpoint.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {unknown} data - The data to include in the request body.
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response.
   */
  async createOrganization(headers: { [key: string]: string }, data: unknown): Promise<APIResponse> {
    return await this.getResponse(this.organizationsEndpoint, ERequestMethod.POST, headers, data);
  }

  /**
   * Retrieves a list of employees for a specific organization by its ID.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {string} orgId - The ID of the organization whose employees are to be retrieved.
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response containing the employees.
   * @throws {Error} - Throws an error if the request fails with a status other than 200.
   */
  async getEmployeesByOrgId(headers: { [key: string]: string }, orgId: string): Promise<APIResponse> {
    const endpoint = `${this.organizationsEndpoint}/${orgId}/employees`;
    const response = await this.getResponse(endpoint, ERequestMethod.GET, headers);
    if (response.status() !== 200) {
      throw new Error(`Failed to get employees by org ID: ${response.status()}`);
    }
    return response;
  }

  /**
   * Creates a new organization and retrieves its ID.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {unknown} data - The data to include in the request body.
   * @returns {Promise<string>} - A promise that resolves to the organization ID.
   * @throws {Error} - Throws an error if the organization creation fails.
   */
  async getNewOrganizationID(headers: { [key: string]: string }, data: unknown): Promise<string> {
    const response = await this.createOrganization(headers, data);
    if (response.status() !== 201) {
      throw new Error('Failed to create employee');
    }
    const { id } = await response.json();
    return id;
  }

  /**
   * Updates an existing organization by sending a PUT request to the organization's endpoint.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {string} organizationId - The ID of the organization to update.
   * @param {unknown} data - The data to include in the request body for the update.
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response.
   * @throws {Error} - Throws an error if the update operation fails with a status other than 200.
   */
  async updateOrganization(headers: { [key: string]: string }, organizationId: string, data: unknown): Promise<APIResponse> {
    const endpoint = `${this.organizationsEndpoint}/${organizationId}`;
    const response = await this.getResponse(endpoint, ERequestMethod.PUT, headers, data);
    if (response.status() !== 200) {
      throw new Error(`Failed to update organization: ${response.status()}`);
    }
    return response;
  }

  /**
   * Deletes an existing organization by sending a DELETE request to the organization's endpoint.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {string} organizationId - The ID of the organization to delete.
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response.
   * @throws {Error} - Throws an error if the delete operation fails with a status other than 204.
   */
  async deleteOrganization(headers: { [key: string]: string }, organizationId: string): Promise<APIResponse> {
    const endpoint = `${this.organizationsEndpoint}/${organizationId}`;
    const response = await this.getResponse(endpoint, ERequestMethod.DELETE, headers);
    if (response.status() !== 204) {
      throw new Error(`Failed to delete organization: ${response.status()}`);
    }
    return response;
  }

  /**
   * Retrieves the data sources for a specific organization.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {string} orgId - The ID of the organization whose data sources are to be retrieved.
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response containing the data sources.
   * @throws {Error} - Throws an error if the request fails with a status other than 200.
   */
  async getDataSources(headers: { [key: string]: string }, orgId: string): Promise<APIResponse> {
    const endpoint = `${this.organizationsEndpoint}/${orgId}/datasources`;
    const response = await this.getResponse(endpoint, ERequestMethod.GET, headers);
    if (response.status() !== 200) {
      throw new Error(`Failed to get data sources: ${response.status()}`);
    }
    return response;
  }

  /**
   * Retrieves the ID of a data source by its name for a specific organization.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {string} orgId - The ID of the organization to which the data source belongs.
   * @param {string} dsName - The name of the data source to retrieve.
   * @returns {Promise<string>} - A promise that resolves to the ID of the data source.
   * @throws {Error} - Throws an error if the data source with the specified name is not found.
   */
  async getDataSourceByName(headers: { [key: string]: string }, orgId: string, dsName: string): Promise<string> {
    const response = await this.getDataSources(headers, orgId);
    const responseBody = (await response.json()) as GetDatasourcesByOrganizationIDResponse;
    const dataSource = responseBody.find(ds => ds.name === dsName);
    if (!dataSource) {
      throw new Error(`Data source with name ${dsName} not found`);
    }
    return dataSource.id;
  }

  /**
   * Forces the reimport of a data source for a specific organization.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {string} orgId - The ID of the organization to which the data source belongs.
   * @param {string} dsId - The ID of the data source to force reimport.
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response.
   * @throws {Error} - Throws an error if the reimport operation fails with a status other than 204.
   */
  async getForceReimportDataSource(headers: { [key: string]: string }, orgId: string, dsId: string): Promise<APIResponse> {
    const endpoint = `${this.organizationsEndpoint}/${orgId}/datasources/${dsId}/force-reimport`;
    debugLog(`Force reimport data source endpoint: ${endpoint}`);

    const response = await this.getResponse(endpoint, ERequestMethod.POST, headers);
    if (response.status() !== 204) {
      throw new Error(`Failed to force reimport data source: ${response.status()}`);
    }
    return response;
  }

  /**
   * Sends a request to add additional admin to an organization.
   *
   * @param {{ [key: string]: string }} headers - The headers to include in the request.
   * @param {string} organizationId - The ID of the organization to which the admin will be added.
   * @param {string} email - The email address of the admin to be added.
   * @param {string} name - The display name of the admin to be added.
   * @returns {Promise<APIResponse>} - A promise that resolves to the API response.
   * @throws {Error} - Throws an error if the request fails with a status other than 200.
   */
  async getAddAdditionalAdminResponse(
    headers: { [key: string]: string },
    organizationId: string,
    email: string,
    name: string
  ): Promise<APIResponse> {
    const endpoint = `${this.organizationsEndpoint}/${organizationId}/add-admin`;
    const data = {
      email: email,
      notes: `Added admin user ${name}`,
      display_name: name,
    };
    const response = await this.getResponse(endpoint, ERequestMethod.POST, headers, data);
    if (response.status() !== 200) {
      throw new Error(`Failed to add additional admin: ${response.status()}`);
    }
    return response;
  }
}
