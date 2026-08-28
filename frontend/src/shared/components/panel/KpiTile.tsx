export type KpiTileProps = {
  label: string;
  value: string;
  caption?: string;
  /** Colours the value and prefixes an arrow, for month-over-month style deltas. */
  trend?: "up" | "down";
};

export function KpiTile({ label, value, caption, trend }: KpiTileProps) {
  const trendClass = trend ? ` ffc-kpi__value--${trend}` : "";

  return (
    <div className={"ffc-kpi"}>
      <span className={"ffc-kpi__label"}>{label}</span>
      <span className={`ffc-kpi__value${trendClass}`}>
        {trend === "up" ? "▲ " : null}
        {trend === "down" ? "▼ " : null}
        {value}
      </span>
      {caption ? <span className={"ffc-kpi__caption"}>{caption}</span> : null}
    </div>
  );
}
