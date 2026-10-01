import { renderHook } from "@testing-library/react";

import { useListDataWithSelectedEntity } from "./useListDataWithSelectedEntity";

type Item = { id?: string; name?: string };

describe("useListDataWithSelectedEntity", () => {
  it("returns the data list unchanged when the entity is already present", () => {
    const data: Item[] = [
      { id: "a", name: "A" },
      { id: "b", name: "B" },
    ];

    const { result } = renderHook(() =>
      useListDataWithSelectedEntity<Item>({ entity: { id: "a" }, data }),
    );

    expect(result.current).toBe(data);
  });

  it("prepends the entity when it is not in the data list", () => {
    const data: Item[] = [{ id: "a", name: "A" }];
    const entity: Item = { id: "z", name: "Z" };

    const { result } = renderHook(() => useListDataWithSelectedEntity<Item>({ entity, data }));

    expect(result.current).toEqual([entity, ...data]);
  });

  it("prepends the unassigned entity when isToShowEmptyValue is true", () => {
    const data: Item[] = [{ id: "a", name: "A" }];
    const unassignedEntity: Item = { id: "unassigned", name: "None" };

    const { result } = renderHook(() =>
      useListDataWithSelectedEntity<Item>({
        entity: { id: "a" },
        data,
        isToShowEmptyValue: true,
        unassignedEntity,
      }),
    );

    expect(result.current).toEqual([unassignedEntity, ...data]);
  });

  it("does not prepend the unassigned entity when isToShowEmptyValue is false", () => {
    const data: Item[] = [{ id: "a", name: "A" }];
    const unassignedEntity: Item = { id: "unassigned", name: "None" };

    const { result } = renderHook(() =>
      useListDataWithSelectedEntity<Item>({
        entity: { id: "a" },
        data,
        isToShowEmptyValue: false,
        unassignedEntity,
      }),
    );

    expect(result.current).toEqual(data);
  });

  it("returns an empty array when data is undefined and no unassigned entity is prepended", () => {
    const { result } = renderHook(() =>
      useListDataWithSelectedEntity<Item>({ entity: null, data: undefined }),
    );

    expect(result.current).toEqual([]);
  });

  it("does not prepend the entity when its id is missing", () => {
    const data: Item[] = [{ id: "a" }];

    const { result } = renderHook(() =>
      useListDataWithSelectedEntity<Item>({ entity: { name: "no id" }, data }),
    );

    expect(result.current).toBe(data);
  });
});
