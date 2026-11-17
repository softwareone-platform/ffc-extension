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
  /** One color per slice, in data order. Kept separate so the data can stay plain JSON. */
  colors: number[];
  height?: number;
  /** Hole size as a percentage of the outer radius. */
  innerRadius?: number;
  /** Text centred in the hole, e.g. the total the slices add up to. */
  centerLabel?: { value: string; caption?: string };
};

// amCharts draws on canvas, so it can't inherit the page font — name the DS one explicitly.
const CENTER_FONT = "Haas Grot Text, Arial, sans-serif";

function centerText({ value, caption }: { value: string; caption?: string }) {
  const total = `[fontSize: 20px fontWeight: 500]${value}[/]`;
  return caption ? `${total}\n[fontSize: 12px #6e7682]${caption}[/]` : total;
}

export function DonutChart({
  data,
  colors,
  height = 150,
  innerRadius = 62,
  centerLabel,
}: DonutChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const seriesRef = useRef<am5percent.PieSeries | null>(null);
  const labelRef = useRef<am5.Label | null>(null);

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

    // Created empty; the effect below fills it, so a new total doesn't rebuild the chart.
    labelRef.current = chart.seriesContainer.children.push(
      am5.Label.new(root, {
        centerX: am5.p50,
        centerY: am5.p50,
        textAlign: "center",
        fontFamily: CENTER_FONT,
        fill: am5.color(0x25282d),
        populateText: false,
        // Hole diameter ≈ height × innerRadius; keep a margin and shrink the text to fit on
        // the small aside donuts instead of letting the caption spill onto the slices.
        maxWidth: height * (innerRadius / 100) * 0.8,
        oversizedBehavior: "fit",
      }),
    );

    seriesRef.current = series;

    return () => {
      seriesRef.current = null;
      labelRef.current = null;
      root.dispose();
    };
  }, [colors, innerRadius, height]);

  useLayoutEffect(() => {
    seriesRef.current?.data.setAll(data);
  }, [data]);

  // Keyed on the strings, not the prop object, so it only re-runs when the text changes —
  // plus the props that rebuild the root and hand it a fresh, empty label.
  const centerValue = centerLabel?.value;
  const centerCaption = centerLabel?.caption;
  useLayoutEffect(() => {
    labelRef.current?.set(
      "text",
      centerValue === undefined ? "" : centerText({ value: centerValue, caption: centerCaption }),
    );
  }, [centerValue, centerCaption, colors, innerRadius, height]);

  return <div ref={containerRef} style={{ width: "100%", height }} />;
}
