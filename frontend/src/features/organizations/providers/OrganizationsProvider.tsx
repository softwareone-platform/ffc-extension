import { createContext, PropsWithChildren, useContext } from "react";

import { OrganizationRead } from "~api/ffc-api-model";

const OrganizationContext = createContext<OrganizationRead | undefined>({} as OrganizationRead);

// eslint-disable-next-line react-refresh/only-export-components
export const useOrganizationContext = () => {
  const context = useContext(OrganizationContext);

  return context;
};

export function OrganizationsProvider({
  children,
  organization,
}: PropsWithChildren & { organization: OrganizationRead }) {
  return (
    <OrganizationContext.Provider value={organization}>{children}</OrganizationContext.Provider>
  );
}
