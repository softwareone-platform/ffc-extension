import { mapAxiosResponseDataList } from "./mapAxiosResponseDataList";

describe("mapAxiosResponseDataList", () => {
  it("returns an empty list when the response data is missing", () => {
    expect(mapAxiosResponseDataList({ data: null })).toEqual({ data: [], total: undefined });
  });

  it.each([
    [
      { total: 5, items: [{ id: "1" }] },
      { data: [{ id: "1" }], total: 5 },
    ],
    [
      { offset: 20, limit: 10, items: [{ id: "1" }, { id: "2" }] },
      { data: [{ id: "1" }, { id: "2" }], total: 22 },
    ],
    [
      { offset: 20, limit: 2, items: [{ id: "1" }, { id: "2" }] },
      { data: [{ id: "1" }, { id: "2" }], total: undefined },
    ],
    [
      { offset: 20, items: [{ id: "1" }] },
      { data: [{ id: "1" }], total: undefined },
    ],
    [
      { total: 0, items: [] },
      { data: [], total: 0 },
    ],
    [{ items: null }, { data: [], total: undefined }],
  ] as const)("maps %j", (responseData, expected) => {
    expect(
      mapAxiosResponseDataList({
        data: responseData as never,
      }),
    ).toEqual(expected);
  });
});
