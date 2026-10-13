import { useLayoutEffect, useRef } from "react";

import * as am5 from "@amcharts/amcharts5";
import * as am5xy from "@amcharts/amcharts5/xy";

import { createChartRoot } from "./chartTheme";

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

    // `{name}` is the series label, `{valueX}`/`{valueY}` is the value axis — vertical charts
    // put the number on Y, horizontal charts on X.
    const tooltipText = horizontal
      ? "[bold]{name}[/]\n{valueX}"
      : "[bold]{name}[/]\n{valueY}";

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

    built.categoryAxis.data.setAll(data);
    built.series.forEach((entry) => entry.data.setAll(data));
  }, [data]);

  return <div ref={containerRef} style={{ width: "100%", height }} />;
}
