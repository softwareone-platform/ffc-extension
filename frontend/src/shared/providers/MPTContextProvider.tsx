/* eslint-disable react-refresh/only-export-components */
import { createContext, PropsWithChildren, useContext, useSyncExternalStore } from "react";

import { useMPTContext } from "@mpt-extension/sdk-react";

export type MPTAuth = {
  user: { id: string };
  account: { id: string; type: string };
};

export type MPTData = {
  isRootPage?: boolean;
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

// Poll for `globalThis.__MPT__` (injected by the host around mount time).
// Give up after 5s so standalone mode doesn't poll forever.
function subscribeToHost(onChange: () => void): () => void {
  if (globalThis.__MPT__ !== undefined) return () => {};
  const stop = () => {
    globalThis.clearInterval(intervalId);
    globalThis.clearTimeout(timeoutId);
  };
  const intervalId = globalThis.setInterval(() => {
    if (globalThis.__MPT__ !== undefined) {
      stop();
      onChange();
    }
  }, 50);
  const timeoutId = globalThis.setTimeout(stop, 5000);
  return stop;
}

function getHostSnapshot(): boolean {
  return globalThis.__MPT__ !== undefined;
}

export function MPTContextProvider({ children }: PropsWithChildren) {
  const hasHost = useHasMPTHost();

  if (!hasHost) {
    return <MPTContextStore.Provider value={{}}>{children}</MPTContextStore.Provider>;
  }

  return <HostContextBridge>{children}</HostContextBridge>;
}

export function useHasMPTHost(): boolean {
  return useSyncExternalStore(subscribeToHost, getHostSnapshot, getHostSnapshot);
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

export function useIsRootPage(): boolean {
  return useContext(MPTContextStore).data?.isRootPage ?? false;
}
