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

// The host injects `globalThis.__MPT__` either before React mounts or shortly
// after. Treat it as an external store: poll until present, then unsubscribe.
function subscribeToHost(onChange: () => void): () => void {
  if (globalThis.__MPT__ !== undefined) return () => {};
  const id = window.setInterval(() => {
    if (globalThis.__MPT__ !== undefined) {
      window.clearInterval(id);
      onChange();
    }
  }, 50);
  return () => window.clearInterval(id);
}

function getHostSnapshot(): boolean {
  return globalThis.__MPT__ !== undefined;
}

export function MPTContextProvider({ children }: PropsWithChildren) {
  const hasHost = useSyncExternalStore(subscribeToHost, getHostSnapshot, getHostSnapshot);

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

declare global {
  interface Window {
    __MPT__?: {
      context?: unknown;
      onChange?: (cb: (data: unknown) => void) => void;
    };
  }
}
export function useStandAloneApp(): boolean {
  return useContext(MPTContextStore).data?.standAloneApp ?? false;
}

