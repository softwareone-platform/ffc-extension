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
  module: {
    type: 'commonjs',
  },
};

export default {
  rootDir: 'src',
  testEnvironment: 'jsdom',
  transformIgnorePatterns: [
    '/node_modules/(?!(@swo|@mpt-extension|axios|@tanstack|react-i18next|zod|zod-i18n-map|@hey-api|@hookform)/)',
  ],
  transform: {
    '^.+\\.[jt]sx?$': ['@swc/jest', swcConfig],
  },
  moduleNameMapper: {
    '\\.(css|scss)$': 'identity-obj-proxy',
    '~api(.*)$': '<rootDir>/api/$1',
    '~app(.*)$': '<rootDir>/app/$1',
    '~features(.*)$': '<rootDir>/features/$1',
    '~organizations(.*)$': '<rootDir>/features/organizations/$1',
    '~entitlements(.*)$': '<rootDir>/features/entitlements/$1',
    '~shared(.*)$': '<rootDir>/shared/$1',
    '~i18n(.*)$': '<rootDir>/i18n/$1',
  },
  setupFilesAfterEnv: ['@testing-library/jest-dom', '../jest.setup.js'],
  testTimeout: 10_000,
  clearMocks: true,
  workerIdleMemoryLimit: '512MB',
};
