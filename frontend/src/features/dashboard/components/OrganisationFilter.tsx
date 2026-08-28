import { useMemo, useState } from "react";

import { Button } from "@swo/design-system/button";
import { Dropdown } from "@swo/design-system/dropdown";

import { useFixedT } from "~shared/hooks/useFixedT";

import { useOrganizationOptionsApi } from "../api";

export function OrganisationFilter() {
  const tFilters = useFixedT("dashboard:filters");
  const { data: organizations } = useOrganizationOptionsApi();
  const [selected, setSelected] = useState<string[]>([]);

  const options = useMemo(
    () =>
      (organizations ?? []).map((organization) => ({
        value: organization.id,
        label: organization.name,
      })),
    [organizations],
  );

  // Undefined while loading, and permanently undefined for affiliates because the query is
  // disabled for them — either way there is nothing to filter by.
  if (!organizations) {
    return null;
  }

  function toggle(value: string) {
    setSelected((current) =>
      current.includes(value) ? current.filter((entry) => entry !== value) : [...current, value],
    );
  }

  const label = selected.length
    ? tFilters("organisationSelected", { count: selected.length })
    : tFilters("organisationAll");

  return (
    <Dropdown value={selected} options={options} onItemSelected={toggle}>
      <Button type={"outline"}>{label}</Button>
    </Dropdown>
  );
}
