import type { useFormatDate } from "~shared/hooks/useFormatDate";

type FormatDate = ReturnType<typeof useFormatDate>;

// Deterministic formatter so specs can assert which raw value was formatted.
export const mockFormatDate = jest.fn<ReturnType<FormatDate>, Parameters<FormatDate>>(
  (value) => `date(${String(value)})`,
);

export const mockFormatDateModule = {
  useFormatDate: () => mockFormatDate,
};
