import { useEffect, useMemo, useState } from "react";

import { Outlet } from "react-router-dom";

import { Button } from "@swo/design-system/button";

import { useMPTEmit } from "@mpt-extension/sdk-react";

import {
  AddOrganizationFormValues,
  AddOrganizationModal,
} from "~features/organizations/components/AddOrganizationModal";
import { PageShell, PageShellNavItem } from "~shared/components/page-shell";
import { useStandAloneApp } from "~shared/providers/MPTContextProvider";

const NAV_ITEMS: PageShellNavItem[] = [
  { path: "/entitlements", label: "Entitlements" },
  { path: "/organizations", label: "Organizations" },
];

export function MainLayout() {
  const [isAddOpen, setIsAddOpen] = useState(false);
  const navItems = useMemo(() => NAV_ITEMS, []);
  const standAloneApp = useStandAloneApp();
  // const standAloneApp = true; // --- FORCE STANDALONE MODE FOR TESTING ---
  const emit = useMPTEmit();

  useEffect(() => {
    if (typeof window.__MPT__ === "undefined") return;
    emit("child-modal", { isOpen: isAddOpen });
  }, [emit, isAddOpen]);

  return (
    <>
      <PageShell>
        {standAloneApp && (
          <PageShell.Header
            items={navItems}
            actions={
              <Button
                type="primary"
                onClick={() => setIsAddOpen(true)}
                testId="add-organization-button"
              >
                Add organization
              </Button>
            }
          />
        )}
        <PageShell.Content>
          <Outlet />
        </PageShell.Content>
      </PageShell>
      <AddOrganizationModal
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        onSubmit={(values: AddOrganizationFormValues) => {
          console.log("[entitlements] add organization submitted", values);
        }}
      />
    </>
  );
}
