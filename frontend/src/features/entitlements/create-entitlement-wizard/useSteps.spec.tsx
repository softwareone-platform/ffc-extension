import { renderHook } from "@testing-library/react";

import { useSteps } from "./useSteps";

describe("useSteps", () => {
  it("returns four steps in fixed order", () => {
    const { result } = renderHook(() => useSteps(false));

    expect(result.current.map((s) => s.title)).toEqual([
      "affiliate:title",
      "dataSource:title",
      "overview:title",
      "summary:title",
    ]);
  });

  it("marks the overview step's next button as a submit button", () => {
    const { result } = renderHook(() => useSteps(false));

    expect(result.current[2].nextButton).toMatchObject({
      label: "add",
      htmlType: "submit",
    });
  });

  it("hides the summary step's next button", () => {
    const { result } = renderHook(() => useSteps(false));

    expect(result.current[3].nextButton).toMatchObject({ isHidden: true });
  });

  it("disables and marks busy every button when isSaving is true", () => {
    const { result } = renderHook(() => useSteps(true));

    for (const step of result.current) {
      expect(step.closeButton).toMatchObject({ isDisabled: true });
      expect(step.backButton).toMatchObject({ isDisabled: true });
      expect(step.nextButton).toMatchObject({ isDisabled: true, isBusy: true });
    }
  });

  it("does not disable buttons when isSaving is false", () => {
    const { result } = renderHook(() => useSteps(false));

    for (const step of result.current) {
      expect(step.nextButton?.isDisabled).toBe(false);
      expect(step.backButton?.isDisabled).toBe(false);
    }
  });
});
