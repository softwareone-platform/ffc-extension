import { useCallback } from "react";

import { useQuery } from "@tanstack/react-query";
import { AxiosRequestConfig } from "axios";

import { http } from "@mpt-extension/sdk";

import { Me } from "~api/ffc-api-model";

const rootPath = "/ops/v1/me";
export function useMeApi() {
  const get = useCallback(async (config?: AxiosRequestConfig<Me>) => {
    return http<Me>({
      method: "GET",
      url: rootPath,
      ...config,
    });
  }, []);

  return useQuery({
    queryKey: ["Me"] as const,
    queryFn: () => get(),
    select: (res) => res.data,
  });
}
