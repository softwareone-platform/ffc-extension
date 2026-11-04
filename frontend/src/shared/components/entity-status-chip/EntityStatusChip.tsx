import { StatusChip } from "@swo/mp-status-chip";

function capitalizeFirstLetter(statusName: string) {
  return String(statusName).charAt(0).toUpperCase() + String(statusName).slice(1);
}

export function Status({ status }: { readonly status: string }) {
  return <StatusChip status={capitalizeFirstLetter(status)} />;
}
