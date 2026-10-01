import { ReactNode } from "react";

import { KpiTile, KpiTileProps, Panel } from "~shared/components/panel";

type MetricPanelProps = {
  title: string;
  className?: string;
  description?: string;
  kpis?: KpiTileProps[];
  trend?: ReactNode;
  aside?: ReactNode;
  asideLabel?: string;
  children?: ReactNode;
};

export function MetricPanel({
  title,
  className,
  description,
  kpis,
  trend,
  aside,
  asideLabel,
  children,
}: MetricPanelProps) {
  const hasSplit = Boolean(trend || aside);

  return (
    <Panel title={title} className={className}>
      {description && <p className={"ffc-panel__description"}>{description}</p>}
      {kpis && (
        <div className={"ffc-kpi-row"}>
          {kpis.map((kpi, index) => (
            <KpiTile key={index} {...kpi} />
          ))}
        </div>
      )}
      {hasSplit && (
        <div className={"ffc-chart-split"}>
          {trend && <div>{trend}</div>}
          {aside && (
            <div className={"ffc-chart-split__aside"}>
              {asideLabel && (
                <span className={"ffc-chart-split__aside-label"}>{asideLabel}</span>
              )}
              {aside}
            </div>
          )}
        </div>
      )}
      {children}
    </Panel>
  );
}
