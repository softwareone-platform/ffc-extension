import { useState } from "react";

import { Button } from "@swo/design-system/button";
import { Checkbox } from "@swo/design-system/checkbox";
import { ConfigurationPanel } from "@swo/design-system/configuration-panel";
import { DatePicker } from "@swo/design-system/date-picker";
import { Icon } from "@swo/design-system/icon";

import { useFixedT } from "~shared/hooks/useFixedT";

const ORGANISATION_STATUSES = ["active", "paid", "trial", "terminated", "deleted"];
const CLOUD_PROVIDERS = ["azure", "aws", "gcp"];

// Default range: rolling 3-month window ending today. Computed once inside useState so the
// initial pair stays stable across re-renders.
function initialRange() {
  const to = new Date();
  const from = new Date(to);
  from.setMonth(from.getMonth() - 3);
  return { from, to };
}

export function FilterSidebar() {
  const tFilters = useFixedT("dashboard:filters");
  const tStatus = useFixedT("dashboard:filters:status");
  const tProvider = useFixedT("dashboard:filters:provider");

  const [isCollapsed, setIsCollapsed] = useState(true);
  const [range, setRange] = useState(initialRange);
  const [statuses, setStatuses] = useState<string[]>(["active"]);
  const [providers, setProviders] = useState<string[]>([]);

  function toggle(list: string[], value: string) {
    return list.includes(value) ? list.filter((entry) => entry !== value) : [...list, value];
  }

  if (isCollapsed) {
    return (
      <button
        type={"button"}
        className={"ffc-filter-sidebar__trigger"}
        data-testid={"ffc-filter-sidebar__trigger"}
        aria-label={tFilters("expand")}
        onClick={() => setIsCollapsed(false)}
      >
        <Icon name={"filter_alt"} size={20} />
      </button>
    );
  }

  return (
    <ConfigurationPanel className={"ffc-filter-sidebar"} title={tFilters("title")}>
      <ConfigurationPanel.Section title={tFilters("timeLabel")}>
        <DatePicker<Date>
          label={tFilters("from")}
          value={range.from}
          maxDate={range.to}
          onChange={(from) => setRange((current) => ({ ...current, from }))}
        />
        <DatePicker<Date>
          label={tFilters("to")}
          value={range.to}
          minDate={range.from}
          onChange={(to) => setRange((current) => ({ ...current, to }))}
        />
      </ConfigurationPanel.Section>
      <ConfigurationPanel.Section title={tFilters("organisationStatus")}>
        {ORGANISATION_STATUSES.map((status) => (
          <Checkbox
            key={status}
            label={tStatus(status)}
            isChecked={statuses.includes(status)}
            onChange={() => setStatuses((current) => toggle(current, status))}
          />
        ))}
      </ConfigurationPanel.Section>
      <ConfigurationPanel.Section title={tFilters("cloudProvider")}>
        {CLOUD_PROVIDERS.map((provider) => (
          <Checkbox
            key={provider}
            label={tProvider(provider)}
            isChecked={providers.includes(provider)}
            onChange={() => setProviders((current) => toggle(current, provider))}
          />
        ))}
      </ConfigurationPanel.Section>
      <ConfigurationPanel.Actions>
        <Button type={"secondary"} onClick={() => setIsCollapsed(true)}>
          {tFilters("collapse")}
        </Button>
        <Button type={"primary"} onClick={() => undefined}>
          {tFilters("apply")}
        </Button>
      </ConfigurationPanel.Actions>
    </ConfigurationPanel>
  );
}
