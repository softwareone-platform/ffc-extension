import { createContext, PropsWithChildren, useContext } from "react";

const StandaloneContext = createContext(false);

export function StandaloneProvider({ children }: PropsWithChildren) {
  return <StandaloneContext.Provider value={true}>{children}</StandaloneContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useIsStandalone() {
  return useContext(StandaloneContext);
}
