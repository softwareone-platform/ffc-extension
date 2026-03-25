export type GetEmployeesByOrganisationIDResponse = [
  {
    email: string;
    display_name: string;
    created_at: string; // ISO date string
    last_login: string; // ISO date string
    roles_count: number;
    id: string; // UUID
  },
];
