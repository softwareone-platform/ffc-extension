import { useLayoutEffect, useRef } from "react";

import * as am5 from "@amcharts/amcharts5";
import * as am5xy from "@amcharts/amcharts5/xy";

import { createChartRoot } from "./chartTheme";

// Monthly rows key the category as an ISO 8601 UTC month start (`2025-01-01T00:00:00Z`).
// Formatting in UTC keeps that month start from rendering as the previous month in negative
// UTC offsets.
const ISO_DATETIME = /^\d{4}-\d{2}-\d{2}T/;
const AXIS_DATE_FORMAT = new Intl.DateTimeFormat("en-US", { month: "short", timeZone: "UTC" });
const TOOLTIP_DATE_FORMAT = new Intl.DateTimeFormat("en-US", {
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

// Extra field written onto every row so tooltips can show the formatted category via a
// `{categoryLabel}` placeholder (amCharts resolves placeholders against the row's data context).
const CATEGORY_LABEL_FIELD = "categoryLabel";

/** Formats ISO datetime categories (`"Jan"` / `"Jan 2025"`); other categories pass through. */
function formatCategory(value: unknown, format: Intl.DateTimeFormat): string {
  if (typeof value === "string" && ISO_DATETIME.test(value)) {
    const date = new Date(value);
    if (!Number.isNaN(date.getTime())) {
      return format.format(date);
    }
  }
  return value == null ? "" : String(value);
}

export type XySeriesKind = "line" | "area" | "column";

export type XySeriesDef = {
  field: string;
  name: string;
  color: number;
  kind: XySeriesKind;
};

export type XyChartRow = Record<string, string | number>;

export type XyChartProps = {
  data: XyChartRow[];
  categoryField: string;
  series: XySeriesDef[];
  height?: number;
  /** Stack series on top of each other (stacked area / stacked column). */
  stacked?: boolean;
  /** Swap the axes so categories run down the side and bars grow rightwards. */
  horizontal?: boolean;
};

type BuiltChart = {
  categoryAxis: am5xy.CategoryAxis<am5xy.AxisRenderer>;
  series: am5xy.XYSeries[];
};

export function XyChart({
  data,
  categoryField,
  series,
  height = 200,
  stacked = false,
  horizontal = false,
}: XyChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const builtRef = useRef<BuiltChart | null>(null);

  // Built from the structural props only. `data` is deliberately not a dependency —
  // recreating the amCharts root on every data change is expensive and restarts the load
  // animation, so the effect below pushes new values into the existing series instead.
  useLayoutEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    const root = createChartRoot(container);
    const chart = root.container.children.push(
      am5xy.XYChart.new(root, {
        panX: false,
        panY: false,
        wheelX: "none",
        wheelY: "none",
        paddingLeft: 0,
        paddingRight: 8,
        paddingTop: 8,
      }),
    );

    const categoryAxis = (horizontal ? chart.yAxes : chart.xAxes).push(
      am5xy.CategoryAxis.new(root, {
        categoryField,
        renderer: horizontal
          ? // Inversed so the first (largest) row renders at the top.
            am5xy.AxisRendererY.new(root, { minGridDistance: 16, inversed: true })
          : am5xy.AxisRendererX.new(root, { minGridDistance: 28 }),
      }),
    );
    const valueAxis = (horizontal ? chart.xAxes : chart.yAxes).push(
      am5xy.ValueAxis.new(root, {
        renderer: horizontal
          ? am5xy.AxisRendererX.new(root, {})
          : am5xy.AxisRendererY.new(root, {}),
      }),
    );

    const labelStyle = { fontSize: 10, fill: am5.color(0x6b7280) };
    categoryAxis.get("renderer").labels.template.setAll(labelStyle);
    valueAxis.get("renderer").labels.template.setAll(labelStyle);

    // Axis labels are created with the placeholder text `"{category}"`, so the adapter reads the
    // real category off the label's data item instead of the incoming text.
    categoryAxis.get("renderer").labels.template.adapters.add("text", (text, target) => {
      const dataItem = target.dataItem as am5.DataItem<am5xy.ICategoryAxisDataItem> | undefined;
      const category = dataItem?.get("category");
      return category ? formatCategory(category, AXIS_DATE_FORMAT) : text;
    });

    // `{categoryLabel}` is the formatted category, `{name}` the series label and
    // `{valueX}`/`{valueY}` the value axis — vertical charts put the number on Y, horizontal
    // charts on X.
    const tooltipText = `{${CATEGORY_LABEL_FIELD}}\n[bold]{name}:[/] ${horizontal ? "{valueX}" : "{valueY}"}`;

    function attachTooltip(entry: am5xy.XYSeries) {
      entry.set(
        "tooltip",
        am5.Tooltip.new(root, {
          labelText: tooltipText,
          autoTextColor: false,
          getFillFromSprite: false,
          pointerOrientation: "horizontal",
        }),
      );
      const tooltip = entry.get("tooltip");
      tooltip?.get("background")?.setAll({
        fill: am5.color(0xffffff),
        fillOpacity: 0.95,
        stroke: am5.color(0xe0e5e8),
      });
      tooltip?.label.setAll({ fill: am5.color(0x25282d), fontSize: 12 });
    }

    const createdSeries = series.map((def) => {
      const settings = {
        name: def.name,
        xAxis: horizontal ? valueAxis : categoryAxis,
        yAxis: horizontal ? categoryAxis : valueAxis,
        stacked,
        fill: am5.color(def.color),
        stroke: am5.color(def.color),
        ...(horizontal
          ? { valueXField: def.field, categoryYField: categoryField }
          : { valueYField: def.field, categoryXField: categoryField }),
      };

      if (def.kind === "column") {
        const columnSeries = chart.series.push(am5xy.ColumnSeries.new(root, settings));
        columnSeries.columns.template.setAll({
          strokeOpacity: 0,
          fillOpacity: 1,
          width: am5.percent(60),
          tooltipText,
        });
        attachTooltip(columnSeries);
        return columnSeries;
      }

      const lineSeries = chart.series.push(am5xy.LineSeries.new(root, settings));
      lineSeries.strokes.template.setAll({ strokeWidth: 2 });
      if (def.kind === "area") {
        lineSeries.fills.template.setAll({ visible: true, fillOpacity: 0.5 });
      }
      // Bullets give hover targets on each data point so the tooltip is easy to invoke on a
      // line chart (otherwise users have to hit the thin stroke).
      lineSeries.bullets.push(() =>
        am5.Bullet.new(root, {
          sprite: am5.Circle.new(root, {
            radius: 4,
            fill: am5.color(def.color),
            stroke: am5.color(0xffffff),
            strokeWidth: 2,
            tooltipText,
          }),
        }),
      );
      attachTooltip(lineSeries);
      return lineSeries;
    });

    // Shared crosshair cursor — snaps the active series bullet to the hovered category so the
    // tooltip appears even if the user doesn't land exactly on a bullet or column.
    chart.set(
      "cursor",
      am5xy.XYCursor.new(root, {
        behavior: "none",
        xAxis: horizontal ? valueAxis : categoryAxis,
        yAxis: horizontal ? categoryAxis : valueAxis,
      }),
    );

    builtRef.current = { categoryAxis, series: createdSeries };

    return () => {
      builtRef.current = null;
      root.dispose();
    };
  }, [categoryField, series, stacked, horizontal]);

  useLayoutEffect(() => {
    const built = builtRef.current;
    if (!built) {
      return;
    }

    const rows = data.map((row) => ({
      ...row,
      [CATEGORY_LABEL_FIELD]: formatCategory(row[categoryField], TOOLTIP_DATE_FORMAT),
    }));
    built.categoryAxis.data.setAll(rows);
    built.series.forEach((entry) => entry.data.setAll(rows));
  }, [data, categoryField]);

  return <div ref={containerRef} style={{ width: "100%", height }} />;
}
