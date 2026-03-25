export interface GetOrganizationByIDResponse {
  name: string;
  currency: string;
  billing_currency: string;
  operations_external_id: string;
  events: {
    created: {
      at: string; // ISO date string
      by: {
        id: string;
        type: string;
        name: string;
      };
    };
    updated: {
      at: string; // ISO date string
      by: {
        id: string;
        type: string;
        name: string;
      };
    };
  };
  id: string;
  linked_organization_id: string;
  status: string;
}
