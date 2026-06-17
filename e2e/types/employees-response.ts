export interface EmployeesResponse {
  employees: [
    {
      deleted_at: 0;
      id: string;
      created_at: number;
      name: string;
      organization_id: string;
      auth_user_id: string;
      default_ssh_key_id: null;
      slack_connected: false;
      jira_connected: false;
      last_login: number;
      user_display_name: string;
      user_email: string;
      assignments: [];
    },
  ];
}

