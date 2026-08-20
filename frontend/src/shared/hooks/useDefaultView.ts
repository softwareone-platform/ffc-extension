export function useDefaultView() {
  return {
    isDefaultView: true,
    selectedView: "default",
    filters: {
      operator: "or",
      value: [{ operator: "neq", field: "status", value: "deleted" }],
    },
    sort: [{ field: "events.updated.at", direction: "desc" }],
  };
}
