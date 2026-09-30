import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { useFixedT } from "~shared/hooks/useFixedT";
import type { UserEvent } from "~test-utils";
import { mockButton, mockDesignSystemButton } from "~test-utils/mocks/designSystemButton";
import { mockFixedT } from "~test-utils/mocks/fixedT";

import { ModalCancelButton } from "./ModalCancelButton";

jest.mock("@swo/design-system/button", () => mockDesignSystemButton);

describe("ModalCancelButton", () => {
  let user: UserEvent;

  beforeEach(() => {
    user = userEvent.setup();
    mockFixedT(jest.mocked(useFixedT));
  });

  it("renders the translated cancel label as a text button", () => {
    render(<ModalCancelButton onClick={jest.fn()} />);

    expect(jest.mocked(useFixedT)).toHaveBeenCalledWith("shared:actions");
    expect(mockButton).toHaveBeenCalledWith(
      expect.objectContaining({ children: "translated:cancel", type: "text" }),
    );
    expect(screen.getByRole("button", { name: "translated:cancel" })).toHaveAttribute(
      "data-type",
      "text",
    );
  });

  it("calls onClick when the button is pressed", async () => {
    const onClick = jest.fn();

    render(<ModalCancelButton onClick={onClick} />);
    await user.click(screen.getByRole("button", { name: "translated:cancel" }));

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("disables the button when isDisabled is true", async () => {
    const onClick = jest.fn();

    render(<ModalCancelButton onClick={onClick} isDisabled />);
    await user.click(screen.getByRole("button", { name: "translated:cancel" }));

    expect(mockButton).toHaveBeenCalledWith(expect.objectContaining({ isDisabled: true }));
    expect(screen.getByRole("button", { name: "translated:cancel" })).toBeDisabled();
    expect(onClick).not.toHaveBeenCalled();
  });
});
