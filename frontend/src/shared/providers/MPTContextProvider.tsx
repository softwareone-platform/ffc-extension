/* eslint-disable react-refresh/only-export-components */
import { createContext, PropsWithChildren, useContext, useEffect, useState } from "react";

import { useMPTContext } from "@mpt-extension/sdk-react";

export type MPTAuth = {
  user: { id: string };
  account: { id: string; type: string };
};

export type MPTData = {
  standAloneApp?: boolean;
  sample?: string;
  [key: string]: unknown;
};

export type MPTContextValue = {
  auth?: MPTAuth;
  data?: MPTData;
};

const MPTContextStore = createContext<MPTContextValue>({});

function HostContextBridge({ children }: PropsWithChildren) {
  const raw = useMPTContext() as MPTContextValue | undefined;
  return <MPTContextStore.Provider value={raw ?? {}}>{children}</MPTContextStore.Provider>;
}

export function MPTContextProvider({ children }: PropsWithChildren) {
  const [hasHost, setHasHost] = useState(globalThis.__MPT__ !== undefined);

  // The host may inject `globalThis.__MPT__` slightly after mount; re-check once.
  useEffect(() => {
    if (hasHost) return;
    if (globalThis.__MPT__ !== undefined) {
      setHasHost(true);
    }
  }, [hasHost]);

  if (!hasHost) {
    return <MPTContextStore.Provider value={{}}>{children}</MPTContextStore.Provider>;
  }

  return <HostContextBridge>{children}</HostContextBridge>;
}

export function useMPT(): MPTContextValue {
  return useContext(MPTContextStore);
}

export function useMPTAuth(): MPTAuth | undefined {
  return useContext(MPTContextStore).auth;
}

export function useMPTData(): MPTData | undefined {
  return useContext(MPTContextStore).data;
}

export function useStandAloneApp(): boolean {
  return useContext(MPTContextStore).data?.standAloneApp ?? false;
}

