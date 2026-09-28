import { renderHook } from "@testing-library/react";
import { AxiosError } from "axios";

import { useFixedT } from "./useFixedT";

import { useErrorDetails } from "./useErrorDetails";

jest.mock("./useFixedT", () => ({
  useFixedT: jest.fn(),
}));

describe("useErrorDetails", () => {
  beforeEach(() => {
    jest.mocked(useFixedT).mockReturnValue(
      ((key: string, params?: { code?: string | number }) => {
        const code = params?.code;
        return code ? `failed:${key}:${code}` : `failed:${key}`;
      }) as unknown as ReturnType<typeof useFixedT>,
    );
  });

  it("returns the translated status code when the response body is missing", () => {
    const { result } = renderHook(() => useErrorDetails("errors"));

    const error = new AxiosError("boom", undefined, undefined, undefined, { status: 500 } as never);

    expect(result.current.getErrorMessage(error)).toBe("failed:failed_with_code:500");
  });

  it("appends a string detail to the translated status code", () => {
    const { result } = renderHook(() => useErrorDetails("errors"));

    const error = new AxiosError("boom", undefined, undefined, undefined, {
      status: 404,
      data: { detail: "not found" },
    } as never);

    expect(result.current.getErrorMessage(error)).toBe(
      "failed:failed_with_code:404\nnot found",
    );
  });
});

