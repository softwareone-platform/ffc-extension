import js from '@eslint/js';
import globals from 'globals';
import jest from 'eslint-plugin-jest';
import jestDom from 'eslint-plugin-jest-dom';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import testingLibrary from 'eslint-plugin-testing-library';
import tseslint from 'typescript-eslint';

/**
 * Flat ESLint config for the frontend (ESLint 9 + React 19 + Vite).
 *
 * Kept type-aware rules off (no `parserOptions.project`) so editors / CI run
 * fast; switch to `tseslint.configs.recommendedTypeChecked` if you need
 * cross-file type-checked lint rules.
 */
export default tseslint.config(
    {
        ignores: ['node_modules/**', 'dist/**', '../static/**', 'coverage/**','src/api/**','src/i18n/**/*.json','package*.json', 'tsconfig.json', 'vite.config.*', 'esbuild.config.*', 'eslint.config.*'],
    },
    {
        files: ['**/*.{ts,tsx,js,mjs,cjs,json}'],
        extends: [js.configs.recommended, ...tseslint.configs.recommended],
        languageOptions: {
            ecmaVersion: 2022,
            sourceType: 'module',
            globals: {
                ...globals.browser,
                ...globals.node,
            },
        },
        plugins: {
            'react-hooks': reactHooks,
            'react-refresh': reactRefresh,
        },
        rules: {
            ...reactHooks.configs.recommended.rules,
            'react-refresh/only-export-components': [
                'warn',
                { allowConstantExport: true },
            ],
            '@typescript-eslint/no-unused-vars': [
                'error',
                {
                    argsIgnorePattern: '^_',
                    varsIgnorePattern: '^_',
                    caughtErrorsIgnorePattern: '^_',
                },
            ],
            'no-unused-vars': 'off',
        },
    },
    {
        // Build/config scripts: allow Node globals + CommonJS-ish patterns.
        files: ['esbuild.config.js', 'vite.config.*', 'eslint.config.*'],
        languageOptions: { globals: { ...globals.node } },
    },
    {
        // Spec files: enable jest / testing-library / jest-dom lint rules.
        // Scoped so app code isn't touched by test-only assertions.
        files: ['**/*.spec.{ts,tsx}', '**/*.spec.mocks.{ts,tsx}', 'src/test-utils/**/*.{ts,tsx}', 'jest.setup.js'],
        plugins: {
            jest,
            'testing-library': testingLibrary,
            'jest-dom': jestDom,
        },
        languageOptions: {
            globals: { ...globals.jest },
        },
        rules: {
            ...jest.configs['flat/recommended'].rules,
            ...testingLibrary.configs['flat/react'].rules,
            ...jestDom.configs['flat/recommended'].rules,
        },
    },
);
