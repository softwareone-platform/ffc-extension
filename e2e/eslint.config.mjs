import eslint from '@eslint/js';
import prettier from 'eslint-config-prettier';
import playwright from 'eslint-plugin-playwright';
import tseslint from 'typescript-eslint';

export default [
  {
    ignores: ['node_modules/**', 'dist/**', 'coverage/**', 'playwright-report/**', 'test-results/**', '**/localforage.min.js'],
  },
  eslint.configs.recommended,
  {
    files: ['**/*.ts', '**/*.tsx'],
    ...(Array.isArray(tseslint.configs.recommendedTypeChecked)
      ? tseslint.configs.recommendedTypeChecked[0]
      : tseslint.configs.recommendedTypeChecked),
    plugins: {
      '@typescript-eslint': tseslint.plugin,
    },
    rules: {
      'no-undef': 'off',
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' }],
    },
  },
  {
    files: ['**/*.js', '**/*.mjs'],
    ...eslint.configs.recommended,
  },
  ...(Array.isArray(playwright.configs['flat/recommended'])
    ? playwright.configs['flat/recommended']
    : [playwright.configs['flat/recommended']]),
  ...(Array.isArray(prettier) ? prettier : [prettier]),
];
