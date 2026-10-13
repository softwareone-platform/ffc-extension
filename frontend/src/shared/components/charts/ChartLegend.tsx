import { ReactNode } from "react";

import { Link } from "react-router-dom";

export type ChartLegendItem = {
  name: string;
  color: number;
  /** When set, the item renders as a `react-router-dom` link to the given path. */
  linkTo?: string;
};

export type ChartLegendProps = {
  items: ChartLegendItem[];
  heading?: string;
  /** Horizontal reads better under a chart; vertical suits a side-by-side key. */
  layout?: "vertical" | "horizontal";
};

function toCssColor(color: number) {
  return `#${color.toString(16).padStart(6, "0")}`;
}

export function ChartLegend({ items, heading, layout = "vertical" }: ChartLegendProps) {
  return (
    <ul className={`ffc-legend ffc-legend--${layout}`}>
      {heading ? <li className={"ffc-legend__heading"}>{heading}</li> : null}
      {items.map((item) => {
        const body: ReactNode = (
          <>
            <span
              className={"ffc-legend__swatch"}
              style={{ background: toCssColor(item.color) }}
            />
            {item.name}
          </>
        );
        return (
          <li key={item.name} className={"ffc-legend__item"}>
            {item.linkTo ? (
              <Link to={item.linkTo} className={"ffc-legend__link"}>
                {body}
              </Link>
            ) : (
              body
            )}
          </li>
        );
      })}
    </ul>
  );
}
