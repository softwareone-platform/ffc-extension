import type { MouseEventHandler, ReactNode } from "react";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { useFixedT } from "~shared/hooks/useFixedT";

import { ModalCancelButton } from "./ModalCancelButton";

type ButtonProps = {
  children?: ReactNode;
  onClick?: MouseEventHandler<HTMLButtonElement>;
  isDisabled?: boolean;
  type?: string;
};

const mockButton = jest.fn() as jest.MockedFunction<(props: ButtonProps) => void>;

jest.mock("@swo/design-system/button", () => ({
  Button: ({ children, onClick, isDisabled, type }: ButtonProps) => {
    mockButton({ children, onClick, isDisabled, type });
    return (
      <button data-testid="cancel-button" onClick={onClick} disabled={isDisabled} data-type={type}>
        {children}
      </button>
    );
  },
}));

describe("ModalCancelButton", () => {
  beforeEach(() => {
    mockButton.mockReset();
    jest
      .mocked(useFixedT)
      .mockReturnValue(((key: string) => `translated:${key}`) as ReturnType<typeof useFixedT>);
  });

  it("renders the translated cancel label as a text button", () => {
    render(<ModalCancelButton onClick={jest.fn()} />);

    expect(jest.mocked(useFixedT)).toHaveBeenCalledWith("shared:actions");
    expect(mockButton).toHaveBeenCalledWith(
      expect.objectContaining({ children: "translated:cancel", type: "text" }),
    );
    expect(screen.getByTestId("cancel-button")).toHaveTextContent("translated:cancel");
    expect(screen.getByTestId("cancel-button")).toHaveAttribute("data-type", "text");
  });

  it("calls onClick when the button is pressed", async () => {
    const user = userEvent.setup();
    const onClick = jest.fn();

    render(<ModalCancelButton onClick={onClick} />);
    await user.click(screen.getByTestId("cancel-button"));

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("disables the button when isDisabled is true", async () => {
    const user = userEvent.setup();
    const onClick = jest.fn();

    render(<ModalCancelButton onClick={onClick} isDisabled />);
    await user.click(screen.getByTestId("cancel-button"));

    expect(mockButton).toHaveBeenCalledWith(expect.objectContaining({ isDisabled: true }));
    expect(screen.getByTestId("cancel-button")).toBeDisabled();
    expect(onClick).not.toHaveBeenCalled();
  });
});
