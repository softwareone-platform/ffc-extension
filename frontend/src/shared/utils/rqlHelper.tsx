import { RqlQuery } from "@swo/rql-client";

export function getCustomQueryString<T extends object>(query: RqlQuery<T>): string {
  const queryString = query
    .toString()
    .split("&")
    .map((param) => {
      if (param.startsWith("order=")) {
        const sOrder = serializeOrderBy<T>(query.order);

        if (sOrder) {
          return `order_by(${sOrder})`;
        }
      }

      return param;
    })
    .join("&");

  return queryString;
}

export function serializeOrderBy<T extends object>(order: RqlQuery<T>["order"]): string {
  if (order.length > 1) {
    return `${order
      .map((props) => {
        if (Array.isArray(props)) {
          const [field, direction] = props;
          return `${direction === "desc" ? "-" : ""}${field}`;
        }
        return props;
      })
      .join(",")}`;
  }

  if (order.length === 1) {
    if (Array.isArray(order[0])) {
      const [field, direction] = order[0];
      return `${direction === "desc" ? "-" : ""}${field}`;
    }
    return order[0];
  }

  return "";
}
