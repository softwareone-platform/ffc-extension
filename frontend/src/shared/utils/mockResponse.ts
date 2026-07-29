import { AxiosResponse } from "axios";

// Sandbox helper: wrap static data in an axios-shaped response so the real
// react-query + RQL-grid stack runs unchanged against mock data. The small
// delay lets components still exercise their loading states.
export function mockResponse<T>(data: T, delayMs = 250): Promise<AxiosResponse<T>> {
  return new Promise((resolve) =>
    setTimeout(() => resolve({ data } as unknown as AxiosResponse<T>), delayMs),
  );
}
