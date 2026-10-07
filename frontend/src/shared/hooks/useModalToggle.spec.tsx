import { act, renderHook } from "@testing-library/react";

import type { ModalCloseResult } from "~shared/components/modal/types";

import { useModalToggle } from "./useModalToggle";

describe("useModalToggle", () => {
  it("starts closed with no data", () => {
    const { result } = renderHook(() => useModalToggle());

    expect(result.current.isOpen).toBe(false);
    expect(result.current.data).toBeNull();
  });

  it("opens with optional data and closes back to null", () => {
    const { result } = renderHook(() => useModalToggle<{ id: string }>());

    act(() => {
      result.current.open({ id: "item-1" });
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.data).toEqual({ id: "item-1" });

    act(() => {
      result.current.close();
    });

    expect(result.current.isOpen).toBe(false);
    expect(result.current.data).toBeNull();
  });

  it("calls onSuccess only when closing with success", () => {
    const onSuccess = jest.fn();
    const { result } = renderHook(() => useModalToggle({ onSuccess }));

    act(() => {
      result.current.close({ success: false } as ModalCloseResult);
    });

    expect(onSuccess).not.toHaveBeenCalled();

    act(() => {
      result.current.close({ success: true } as ModalCloseResult);
    });

    expect(onSuccess).toHaveBeenCalledTimes(1);
  });
});
