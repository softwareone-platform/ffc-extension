// @mpt-extension/sdk ships an ESM-only export condition, so require() cannot
// resolve the real module in Jest's CJS mode. This root-level __mocks__ file
// replaces it globally for every test — no per-spec jest.mock needed.
export const setup = jest.fn();
export const http = jest.fn();
