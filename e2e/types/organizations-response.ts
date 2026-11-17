export type OrganizationsResponse = {
  items: {
    id: string;
    name: string;
    status: string;
    events: { updated: { at: string } };
  }[];
  total: number;
  offset: number;
  limit: number;
};
