import { GridCellSimple } from "@swo/design-system/grid";
import { StatusChip } from "@swo/mp-status-chip";

function capitalizeFirstLetter(statusName: string) {
  return (
    String(statusName).charAt(0).toUpperCase() + String(statusName).slice(1)
  );
}

export function Status<T>({ item }: { item: T & { status: string } }) {
  return <StatusChip status={capitalizeFirstLetter(item.status)} />;
}
