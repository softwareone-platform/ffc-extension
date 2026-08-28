import * as am5 from "@amcharts/amcharts5";
import am5themes_Animated from "@amcharts/amcharts5/themes/Animated";

// Raw hex rather than @swo/design-tokens: amCharts needs numeric colours up front, while
// the tokens are CSS custom properties that only resolve once the stylesheet has applied.
export const CHART_COLORS = {
  blue: 0x3f6ed8,
  blueLight: 0x86a7ec,
  navy: 0x1f3d7a,
  green: 0x3fa650,
  yellow: 0xf0c33c,
  orange: 0xe07a3f,
  gray: 0x9aa5b1,
} as const;

export const PROVIDER_COLORS = [CHART_COLORS.blue, CHART_COLORS.orange, CHART_COLORS.green];

// amCharts is used on its attribution tier here, matching the other SWO frontends (none of
// them call addLicense either), so charts render a small "Chart by amCharts" link. Drop a
// purchased key into am5.addLicense(...) below to remove it — don't hide the logo instead.
export function createChartRoot(container: HTMLElement): am5.Root {
  const root = am5.Root.new(container);
  root.setThemes([am5themes_Animated.new(root)]);
  return root;
}
