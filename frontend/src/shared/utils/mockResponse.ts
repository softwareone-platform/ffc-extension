import { AxiosResponse } from "axios";

// Sandbox helper: wrap static data in an axios-shaped response so react-query and any other
// consumer that reads `response.data` runs unchanged against mock data. The small delay lets
// components exercise their loading states, matching what a real network round-trip would.
export function mockResponse<T>(data: T, delayMs = 250): Promise<AxiosResponse<T>> {
  return new Promise((resolve) =>
    setTimeout(() => resolve({ data } as unknown as AxiosResponse<T>), delayMs),
  );
}
