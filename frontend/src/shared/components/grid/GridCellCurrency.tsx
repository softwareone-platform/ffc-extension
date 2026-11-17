import { GridCellSimple, GridCellTitleSubtitle } from "@swo/design-system/grid";
import { DisplayValue } from "@swo/design-system/utils";

import { useFormatMoney } from "~shared/utils/NumberUtils";

export interface GridCellCurrencyProps {
  readonly value?: number | null;
  readonly currency?: string | null;
}

export function GridCellCurrency({ value, currency }: GridCellCurrencyProps) {
  const format = useFormatMoney(currency, false);

  if (!currency) {
    return (
      <GridCellSimple>
        <DisplayValue value={value} transform={format} context="financial" />
      </GridCellSimple>
    );
  }

  return (
    <GridCellTitleSubtitle
      title={<DisplayValue value={value} transform={format} context="financial" />}
      subtitle={<DisplayValue value={currency} />}
    ></GridCellTitleSubtitle>
  );
}
