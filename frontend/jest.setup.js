import {jest} from '@jest/globals';
import {TextEncoder, TextDecoder} from 'node:util';

// jsdom lacks TextEncoder/TextDecoder; react-router-dom needs them at import time.
Object.assign(globalThis, {TextEncoder, TextDecoder});

// Global node_modules stubs are auto-discovered from <root>/__mocks__/:
//   - @mpt-extension/sdk        → __mocks__/@mpt-extension/sdk.ts
//   - react-router-dom          → __mocks__/react-router-dom.tsx
//   - react-i18next             → __mocks__/react-i18next.tsx
//   - @swo/design-system/utils  → __mocks__/@swo/design-system/utils.tsx

// User-module mock (aliased path — not eligible for auto __mocks__/, keep here).
const identityFn = key => key;
jest.mock('~shared/hooks/useFixedT', () => {
  return { useFixedT: jest.fn(() => identityFn) };
});

global.jest = jest;
