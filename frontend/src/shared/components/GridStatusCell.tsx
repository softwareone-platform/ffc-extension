import { GridCellSimple } from "@swo/design-system/grid";
import { StatusChip } from "@swo/mp-status-chip";

function capitalizeFirstLetter(statusName: string) {
  return (
    String(statusName).charAt(0).toUpperCase() + String(statusName).slice(1)
  );
}

export function GridStatusCell<T>({ item }: { item: T & { status: string } }) {
  return (
    <GridCellSimple>
      <StatusChip status={capitalizeFirstLetter(item.status)} />
    </GridCellSimple>
  );
}
