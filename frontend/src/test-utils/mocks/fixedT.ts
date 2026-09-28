// `~shared/hooks/useFixedT` is globally mocked to an identity translator in `jest.setup.js`.
// Use `mockFixedT(jest.mocked(useFixedT))` when a spec needs deterministic translated output.
// If the code under test imports `./useFixedT` relatively (not via `~shared/…`), locally
// `jest.mock("./useFixedT", () => ({ useFixedT: jest.fn() }))` first, then drive with mockFixedT.
type FixedTParams = Record<string, string | number | boolean | undefined>;

type MockTranslate = (key: string, params?: FixedTParams) => string;

export function createFixedT(prefix = "translated"): MockTranslate {
  return (key) => `${prefix}:${key}`;
}

export function mockFixedT<T extends (keyPrefix: string) => unknown>(
  mockedUseFixedT: jest.MockedFunction<T>,
  translate: MockTranslate = createFixedT(),
): MockTranslate {
  mockedUseFixedT.mockReturnValue(translate as ReturnType<T>);
  return translate;
}
