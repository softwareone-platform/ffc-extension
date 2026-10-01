import { renderHook } from "@testing-library/react";

import { useNotifyParentChildModal } from "./useNotifyParentChildModal";

const mockEmit = jest.fn();
const mockUseHasMPTHost = jest.fn();

jest.mock(
  "@mpt-extension/sdk-react",
  () => ({
    useMPTEmit: () => mockEmit,
  }),
  { virtual: true },
);

jest.mock("~shared/providers/MPTContextProvider", () => ({
  useHasMPTHost: () => mockUseHasMPTHost(),
}));

describe("useNotifyParentChildModal", () => {
  it("does nothing when there is no MPT host", () => {
    mockUseHasMPTHost.mockReturnValue(false);

    renderHook(() => useNotifyParentChildModal(true));

    expect(mockEmit).not.toHaveBeenCalled();
  });

  it("does nothing when the modal is closed", () => {
    mockUseHasMPTHost.mockReturnValue(true);

    renderHook(() => useNotifyParentChildModal(false));

    expect(mockEmit).not.toHaveBeenCalled();
  });

  it("emits an open event when the modal opens", () => {
    mockUseHasMPTHost.mockReturnValue(true);

    renderHook(() => useNotifyParentChildModal(true));

    expect(mockEmit).toHaveBeenCalledWith("child-modal", { isOpen: true });
  });

  it("emits a close event when the open modal unmounts", () => {
    mockUseHasMPTHost.mockReturnValue(true);

    const { unmount } = renderHook(() => useNotifyParentChildModal(true));

    mockEmit.mockClear();
    unmount();

    expect(mockEmit).toHaveBeenCalledWith("child-modal", { isOpen: false });
  });

  it("emits a close event when rerendering from open to closed", () => {
    mockUseHasMPTHost.mockReturnValue(true);

    const { rerender } = renderHook(({ isOpen }) => useNotifyParentChildModal(isOpen), {
      initialProps: { isOpen: true },
    });

    mockEmit.mockClear();
    rerender({ isOpen: false });

    expect(mockEmit).toHaveBeenCalledWith("child-modal", { isOpen: false });
  });
});
