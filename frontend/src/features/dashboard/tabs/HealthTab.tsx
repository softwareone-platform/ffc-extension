import { useFixedT } from "~shared/hooks/useFixedT";

import { ComingSoonPanel } from "../components/ComingSoonPanel";

export function HealthTab() {
  const tTabs = useFixedT("dashboard:tabs");
  return <ComingSoonPanel title={tTabs("health")} />;
}
