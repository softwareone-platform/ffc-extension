export type ChartLegendItem = {
  name: string;
  color: number;
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
      {items.map((item) => (
        <li key={item.name} className={"ffc-legend__item"}>
          <span className={"ffc-legend__swatch"} style={{ background: toCssColor(item.color) }} />
          {item.name}
        </li>
      ))}
    </ul>
  );
}
