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
