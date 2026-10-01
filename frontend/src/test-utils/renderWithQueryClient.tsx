import type { PropsWithChildren, ReactElement } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";

export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

export function createQueryClientWrapper(queryClient: QueryClient = createTestQueryClient()) {
  function QueryClientWrapper({ children }: PropsWithChildren) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  }

  return QueryClientWrapper;
}

export function renderWithQueryClient(
  ui: ReactElement,
  queryClient: QueryClient = createTestQueryClient(),
) {
  return {
    queryClient,
    ...render(ui, { wrapper: createQueryClientWrapper(queryClient) }),
  };
}
