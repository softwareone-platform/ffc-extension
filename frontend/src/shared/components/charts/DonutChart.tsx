import { useLayoutEffect, useRef } from "react";

import * as am5 from "@amcharts/amcharts5";
import * as am5percent from "@amcharts/amcharts5/percent";

import { createChartRoot } from "./chartTheme";

export type DonutDatum = {
  category: string;
  value: number;
};

export type DonutChartProps = {
  data: DonutDatum[];
  /** One colour per slice, in data order. Kept separate so the data can stay plain JSON. */
  colors: number[];
  height?: number;
  /** Hole size as a percentage of the outer radius. */
  innerRadius?: number;
};

export function DonutChart({ data, colors, height = 150, innerRadius = 62 }: DonutChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const seriesRef = useRef<am5percent.PieSeries | null>(null);

  // See the note in XyChart: `data` is applied by the second effect so a data change
  // updates the existing series rather than rebuilding the whole root.
  useLayoutEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    const root = createChartRoot(container);
    const chart = root.container.children.push(
      am5percent.PieChart.new(root, {
        innerRadius: am5.percent(innerRadius),
        paddingTop: 0,
        paddingBottom: 0,
      }),
    );

    const series = chart.series.push(
      am5percent.PieSeries.new(root, {
        valueField: "value",
        categoryField: "category",
        alignLabels: false,
      }),
    );

    series.set("colors", am5.ColorSet.new(root, { colors: colors.map((c) => am5.color(c)) }));
    series.labels.template.set("forceHidden", true);
    series.ticks.template.set("forceHidden", true);
    series.slices.template.setAll({ strokeOpacity: 0 });

    seriesRef.current = series;

    return () => {
      seriesRef.current = null;
      root.dispose();
    };
  }, [colors, innerRadius]);

  useLayoutEffect(() => {
    seriesRef.current?.data.setAll(data);
  }, [data]);

  return <div ref={containerRef} style={{ width: "100%", height }} />;
}
