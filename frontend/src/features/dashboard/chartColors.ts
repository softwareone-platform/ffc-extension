// amCharts palettes store colours as numbers; inline styles need the CSS hex form.
export function toCssColor(color: number) {
  return `#${color.toString(16).padStart(6, "0")}`;
}
