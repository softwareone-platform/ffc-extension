/* eslint-disable react-refresh/only-export-components */
import { createContext, PropsWithChildren, useContext, useSyncExternalStore } from "react";

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

// Poll for `globalThis.__MPT__` (injected by the host around mount time).
// Give up after 5s so standalone mode doesn't poll forever.
function subscribeToHost(onChange: () => void): () => void {
  if (globalThis.__MPT__ !== undefined) return () => {};
  const stop = () => {
    window.clearInterval(intervalId);
    window.clearTimeout(timeoutId);
  };
  const intervalId = window.setInterval(() => {
    if (globalThis.__MPT__ !== undefined) {
      stop();
      onChange();
    }
  }, 50);
  const timeoutId = window.setTimeout(stop, 5000);
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

export function useStandAloneApp(): boolean {
  return useContext(MPTContextStore).data?.standAloneApp ?? false;
}

