import type { EmployeeRead } from "~api/ffc-api-model";

export function makeEmployee(overrides: Partial<EmployeeRead> = {}): EmployeeRead {
  return {
    id: "emp-1",
    email: "user@example.com",
    display_name: "User One",
    is_admin: false,
    roles_count: 2,
    last_login: "2026-01-01T00:00:00Z",
    created_at: "2025-12-01T00:00:00Z",
    ...overrides,
  } as EmployeeRead;
}
