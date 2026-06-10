import { Control, Controller, FieldValues, Path } from "react-hook-form";

import { Input, InputProps } from "@swo/design-system/input";

export type ControlledInputProps<T extends FieldValues = FieldValues> = Omit<
  InputProps,
  "name" | "value" | "onChange"
> & {
  name: Path<T>;
  control: Control<T>;
};

export function ControlledInput<T extends FieldValues = FieldValues>({
  control,
  name,
  ...props
}: ControlledInputProps<T>) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => (
        <Input
          {...props}
          name={name}
          variant={fieldState.invalid ? "error" : props.variant}
          value={field.value ?? ""}
          onChange={field.onChange}
          errorMessage={fieldState.error?.message}
        />
      )}
    />
  );
}
