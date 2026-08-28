import { useState } from "react";

import { Button } from "@swo/design-system/button";
import { Checkbox } from "@swo/design-system/checkbox";
import { Select } from "@swo/design-system/select";

import { useFixedT } from "~shared/hooks/useFixedT";

const TIME_RANGES = ["last3Months", "last6Months", "last12Months", "yearToDate"];
const ORGANISATION_STATUSES = ["active", "paid", "trial", "terminated", "deleted"];
const CLOUD_PROVIDERS = ["azure", "aws", "gcp"];

export function FilterSidebar() {
  const tFilters = useFixedT("dashboard:filters");
  const tTime = useFixedT("dashboard:filters:time");
  const tStatus = useFixedT("dashboard:filters:status");
  const tProvider = useFixedT("dashboard:filters:provider");

  const [timeRange, setTimeRange] = useState(TIME_RANGES[0]);
  const [statuses, setStatuses] = useState<string[]>(["active"]);
  const [providers, setProviders] = useState<string[]>([]);

  function toggle(list: string[], value: string) {
    return list.includes(value) ? list.filter((entry) => entry !== value) : [...list, value];
  }

  return (
    <aside className={"ffc-filter-panel"}>
      <h2 className={"ffc-filter-panel__title"}>{tFilters("title")}</h2>

      <div className={"ffc-filter-panel__group"}>
        <Select
          controlLabel={tFilters("timeLabel")}
          value={timeRange}
          options={TIME_RANGES.map((range) => ({ label: tTime(range), value: range }))}
          onChange={setTimeRange}
        />
      </div>

      <div className={"ffc-filter-panel__group"}>
        <span className={"ffc-filter-panel__label"}>{tFilters("organisationStatus")}</span>
        {ORGANISATION_STATUSES.map((status) => (
          <Checkbox
            key={status}
            label={tStatus(status)}
            isChecked={statuses.includes(status)}
            onChange={() => setStatuses((current) => toggle(current, status))}
          />
        ))}
      </div>

      <div className={"ffc-filter-panel__group"}>
        <span className={"ffc-filter-panel__label"}>{tFilters("cloudProvider")}</span>
        {CLOUD_PROVIDERS.map((provider) => (
          <Checkbox
            key={provider}
            label={tProvider(provider)}
            isChecked={providers.includes(provider)}
            onChange={() => setProviders((current) => toggle(current, provider))}
          />
        ))}
      </div>

      <Button type={"primary"} onClick={() => undefined}>
        {tFilters("apply")}
      </Button>
    </aside>
  );
}
