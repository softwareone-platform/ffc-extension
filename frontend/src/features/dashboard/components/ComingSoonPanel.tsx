import { useFixedT } from "~shared/hooks/useFixedT";

export function ComingSoonPanel({ title }: { title: string }) {
  const tComingSoon = useFixedT("dashboard:comingSoon");

  return (
    <div className={"ffc-empty-panel"}>
      <h3 className={"ffc-panel__title"}>{title}</h3>
      <p>{tComingSoon("description")}</p>
    </div>
  );
}
