import type { ChangeEvent } from "react";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useForm, useWatch } from "react-hook-form";

import { ControlledInput } from "./ControlledInput";

type MockInputProps = {
  name?: string;
  value?: string;
  variant?: string;
  errorMessage?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
};

type FormValues = {
  name?: string;
};

const mockInput = jest.fn() as jest.MockedFunction<(props: MockInputProps) => void>;

jest.mock("@swo/design-system/input", () => ({
  Input: ({ name, value, variant, errorMessage, onChange, placeholder }: MockInputProps) => {
    mockInput({ name, value, variant, errorMessage, onChange, placeholder });

    return (
      <>
        <input
          data-testid="controlled-input"
          name={name}
          value={value}
          placeholder={placeholder}
          onChange={(event: ChangeEvent<HTMLInputElement>) => onChange?.(event.target.value)}
        />
        <div data-testid="variant">{variant ?? ""}</div>
        <div data-testid="current-value">{value}</div>
        {errorMessage ? <div data-testid="error-message">{errorMessage}</div> : null}
      </>
    );
  },
}));

function ControlledInputHarness({
  defaultValue,
  variant,
}: {
  defaultValue?: string;
  variant?: string;
}) {
  const { control, setError } = useForm<FormValues>({
    defaultValues: { name: defaultValue },
  });
  const value = useWatch({ control, name: "name" });

  return (
    <>
      <ControlledInput
        control={control}
        name="name"
        placeholder="Name"
        variant={variant as never}
      />
      <button onClick={() => setError("name", { message: "Name is required" })}>set error</button>
      <div data-testid="watched-value">{value ?? ""}</div>
    </>
  );
}

describe("ControlledInput", () => {
  beforeEach(() => {
    mockInput.mockReset();
  });

  it("normalizes an undefined field value to an empty string and forwards the field name", () => {
    render(<ControlledInputHarness />);

    expect(screen.getByTestId("controlled-input")).toHaveAttribute("name", "name");
    expect(screen.getByTestId("current-value")).toHaveTextContent("");
    expect(mockInput.mock.lastCall?.[0].placeholder).toBe("Name");
  });

  it("preserves the provided variant while the field is valid", () => {
    render(<ControlledInputHarness variant="success" />);

    expect(screen.getByTestId("variant")).toHaveTextContent("success");
  });

  it("updates the form value when the input changes", async () => {
    const user = userEvent.setup();

    render(<ControlledInputHarness />);

    await user.type(screen.getByTestId("controlled-input"), "Alice");

    expect(screen.getByTestId("watched-value")).toHaveTextContent("Alice");
  });

  it("switches to the error variant and exposes the validation message when invalid", async () => {
    const user = userEvent.setup();

    render(<ControlledInputHarness variant="success" />);

    await user.click(screen.getByRole("button", { name: "set error" }));

    expect(screen.getByTestId("variant")).toHaveTextContent("error");
    expect(screen.getByTestId("error-message")).toHaveTextContent("Name is required");
  });
});
