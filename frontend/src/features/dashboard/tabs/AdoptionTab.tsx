import { useFixedT } from "~shared/hooks/useFixedT";

import { ComingSoonPanel } from "../components/ComingSoonPanel";

export function AdoptionTab() {
  const tTabs = useFixedT("dashboard:tabs");
  return <ComingSoonPanel title={tTabs("adoption")} />;
}
