import { renderHook } from "@testing-library/react";
import { AxiosError } from "axios";

import { mockFixedT } from "~test-utils/mocks/fixedT";

import { useErrorDetails } from "./useErrorDetails";
import { useFixedT } from "./useFixedT";

jest.mock("./useFixedT", () => ({
  useFixedT: jest.fn(),
}));

describe("useErrorDetails", () => {
  beforeEach(() => {
    mockFixedT(jest.mocked(useFixedT), (key, params) => {
      const code = params?.code;

      return code ? `failed:${key}:${code}` : `failed:${key}`;
    });
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

    expect(result.current.getErrorMessage(error)).toBe("failed:failed_with_code:404\nnot found");
  });

  it("ignores non-string details and returns only the status code message", () => {
    const { result } = renderHook(() => useErrorDetails("errors"));

    const error = new AxiosError("boom", undefined, undefined, undefined, {
      status: 400,
      data: { detail: ["first", "second"] },
    } as never);

    expect(result.current.getErrorMessage(error)).toBe("failed:failed_with_code:400");
  });
});
