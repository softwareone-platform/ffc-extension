import { GridCellTitleSubtitle } from "@swo/design-system/grid";
import { DisplayValue, useFormatDate } from "@swo/design-system/utils";

// import { useFormatDate } from "../../hooks/useFormatDate";
import { useFormatTime } from "../../hooks/useFormatTime";

export interface GridCellDateProps {
  value?: Date | string | null;
}

export function GridCellDate({ value }: GridCellDateProps) {
  const formatDate = useFormatDate();
  const formatTime = useFormatTime();

  return (
    <GridCellTitleSubtitle
      title={<DisplayValue value={value} transform={formatDate} />}
      subtitle={<DisplayValue value={value} transform={formatTime} />}
    />
  );
}
