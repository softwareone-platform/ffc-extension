import {jest} from '@jest/globals';
import {TextEncoder, TextDecoder} from 'node:util';

// jsdom lacks TextEncoder/TextDecoder; react-router-dom needs them at import time.
Object.assign(globalThis, {TextEncoder, TextDecoder});

// Shared node_modules stubs live in <root>/__mocks__/. Enable only the ones
// that need deterministic global activation across specs.
jest.mock('@mpt-extension/sdk', () => ({
  setup: jest.fn(),
  http: jest.fn(),
}), { virtual: true });
jest.mock('@swo/design-system/utils');

// jsdom does not implement ResizeObserver, but some design-system components expect it during render.
if (!globalThis.ResizeObserver) {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}

    unobserve() {}

    disconnect() {}
  };
}

// User-module mock (aliased path — not eligible for root __mocks__/, keep here).
const identityFn = key => key;
jest.mock('~shared/hooks/useFixedT', () => {
  return { useFixedT: jest.fn(() => identityFn) };
});

global.jest = jest;
