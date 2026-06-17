/* eslint-disable react-refresh/only-export-components */
import { PropsWithChildren, createContext, useContext } from "react";

const StandaloneShellContext = createContext(false);

export function StandaloneShellProvider({ children }: PropsWithChildren) {
  return (
    <StandaloneShellContext.Provider value={true}>{children}</StandaloneShellContext.Provider>
  );
}

export function useIsStandaloneShell() {
  return useContext(StandaloneShellContext);
}
