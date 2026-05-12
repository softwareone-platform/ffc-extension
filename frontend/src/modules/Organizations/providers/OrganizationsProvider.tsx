import { useQuery } from "@tanstack/react-query";
import { createContext, PropsWithChildren, useContext, useMemo } from "react";
import { useOrganizationsApi } from "../hooks/useOrganizationsApi";
import { OrganizationRead } from "@swo/ffc-api-model";

const OrganizationContext = createContext<OrganizationRead | undefined>(
  {} as OrganizationRead,
);

export const useOrganizationContext = () => {
  const context = useContext(OrganizationContext);
//   if (context === undefined) {
//     throw new Error(
//       "useOrganizationContext must be used within a OrganizationsProvider",
//     );
//   }
  return context;
};

export function OrganizationsProvider({
  children,
  organization,
}: PropsWithChildren & { organization: OrganizationRead }) {
//   const { get } = useOrganizationsApi();
//   const entityQueryKey = useMemo(
//     () => ["Organizations", "Details", organizationId],
//     ["Organizations", organizationId],
//   );

//   const { data: organization, isLoading } = useQuery({
//     queryKey: entityQueryKey,
//     queryFn: () => get(organizationId!),
//     select: (res) => res.data,
//   });

  return (
    <OrganizationContext.Provider value={organization}>
      {children}
    </OrganizationContext.Provider>
  );
}
