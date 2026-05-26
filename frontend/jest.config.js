import { createDefaultEsmPreset } from "ts-jest";
const presetConfig = createDefaultEsmPreset({});

const swcConfig = {
  jsc: {
    parser: {
      syntax: 'typescript',
      tsx: true,
      decorators: false,
      dynamicImport: true,
    },
    transform: {
      react: { runtime: 'automatic' },
    },
    target: 'es2022',
  },
};

export default {
  ...presetConfig,
  rootDir: 'src',
  testEnvironment: 'jsdom',
  transformIgnorePatterns: [],
  transform: {
    '^.+\\.[jt]sx?$': ['@swc/jest', swcConfig],
  },
  moduleNameMapper: {
    '\\.(css|scss)$': 'identity-obj-proxy',
    '~app(.*)$': '<rootDir>/app/$1',
    '~features(.*)$': '<rootDir>/features/$1',
    '~organizations(.*)$': '<rootDir>/features/organizations/$1',
    '~entitlements(.*)$': '<rootDir>/features/entitlements/$1',
    '~shared(.*)$': '<rootDir>/shared/$1',
    '~styles(.*)$': '<rootDir>/styles/$1',
  },
  setupFilesAfterEnv: ['@testing-library/jest-dom', '../jest.setup.js'],
  testTimeout: 10_000,
  workerIdleMemoryLimit: '512MB',
};
