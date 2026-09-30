import type { RqlQuery } from "@swo/rql-client";

import { getCustomQueryString, serializeOrderBy } from "./rqlHelper";

type OrderValue = Array<string | [string, "asc" | "desc"]>;

type SerializeOrderCase = {
  order: OrderValue;
  expected: string;
};

function makeQuery<T extends object>(queryString: string, order: OrderValue): RqlQuery<T> {
  return {
    order,
    toString: () => queryString,
  } as unknown as RqlQuery<T>;
}

describe("rqlHelper", () => {
  const serializeOrderCases: SerializeOrderCase[] = [
    { order: [], expected: "" },
    { order: ["name"], expected: "name" },
    { order: [["name", "asc"]], expected: "name" },
    { order: [["name", "desc"]], expected: "-name" },
    {
      order: [
        ["name", "asc"],
        ["created_at", "desc"],
      ],
      expected: "name,-created_at",
    },
    { order: ["name", ["created_at", "desc"]], expected: "name,-created_at" },
  ];

  it("returns an empty string when no query is provided", () => {
    expect(getCustomQueryString()).toBe("");
  });

  it("keeps non-order parameters unchanged", () => {
    const query = makeQuery("limit=10&filter=eq(name,test)", []);

    expect(getCustomQueryString(query)).toBe("?limit=10&filter=eq(name,test)");
  });

  it("rewrites the order parameter using the serialized order definition", () => {
    const query = makeQuery("limit=10&order=name&offset=20", ["name", ["created_at", "desc"]]);

    expect(getCustomQueryString(query)).toBe("?limit=10&order_by(name,-created_at)&offset=20");
  });

  it("keeps the original order parameter when no serialized order is available", () => {
    const query = makeQuery("order=&limit=10", []);

    expect(getCustomQueryString(query)).toBe("?order=&limit=10");
  });

  it.each(serializeOrderCases)("serializeOrderBy($order)", ({ order, expected }) => {
    expect(serializeOrderBy(order)).toBe(expected);
  });
});
