import { useFixedT } from "~shared/hooks/useFixedT";

export function Dashboard() {
  const tDashboard = useFixedT("dashboard");

  return <h2>{tDashboard("title")}</h2>;
}
