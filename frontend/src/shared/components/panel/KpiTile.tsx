import { ReactNode } from "react";

import { Link } from "react-router-dom";

import { Card } from "@swo/design-system/card";
import { Icon } from "@swo/design-system/icon";

export type KpiTileProps = {
  label: string;
  value: string;
  caption?: string;
  /** Colours the value: `up` = positive (green), `down` = negative (red). No glyph. */
  trend?: "up" | "down";
  /** When set, the tile renders as a `react-router-dom` link with a right-chevron affordance. */
  linkTo?: string;
};

export function KpiTile({ label, value, caption, trend, linkTo }: KpiTileProps) {
  const trendClass = trend ? ` ffc-kpi--${trend}` : "";

  const content: ReactNode = (
    <Card className={`ffc-kpi${trendClass}`}>
      <div className={"ffc-kpi__text"}>
        <span className={"ffc-kpi__label"}>{label}</span>
        <span className={"ffc-kpi__value"}>{value}</span>
        {caption ? <span className={"ffc-kpi__caption"}>{caption}</span> : null}
      </div>
      {linkTo ? (
        <Icon name={"arrow_forward_ios"} size={16} className={"ffc-kpi__arrow"} />
      ) : null}
    </Card>
  );

  if (linkTo) {
    return (
      <Link to={linkTo} className={"ffc-kpi__link"}>
        {content}
      </Link>
    );
  }

  return content;
}
