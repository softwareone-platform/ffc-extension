/**
 * This configuration extends the default one and provides
 * coverage calculation in cobertura and html format
 * as well as junit test result (to be consumed in CI)
 **/

import jestConfig from './jest.config.js';

const appName = 'ffc-extension';

const normalizedAppName = appName.replace(/\//g, '-');

export default {
  ...jestConfig,
  collectCoverage: true,
  moduleFileExtensions: ['ts', 'tsx', 'js', 'json'],
  collectCoverageFrom: ['<rootDir>/**/*.{js,jsx,ts,tsx}'],
  coverageReporters: [
    'text',
    'cobertura',
    'html',
    ['lcov', { projectRoot: '..', file: '../../lcov.info' }],
    'text-summary',
  ],
  coverageDirectory: '<rootDir>/../coverage',
  coveragePathIgnorePatterns: [
    '\\.d\\.ts',
    '\\.html$',
    'i18n',
    'tests',
    'coverage',
    'TestUtils.tsx',
    'Root.tsx',
    'app.tsx',
    '\\.spec\\.ts$',
    '\\.spec\\.tsx$',
  ],
  reporters: [
    'default',
    [
      'jest-junit',
      {
        outputDirectory: './test-results',
        outputName: `${normalizedAppName}-results.xml`,
      },
    ],
    [
      'jest-html-reporter',
      {
        pageTitle: appName,
        outputPath: `test-results/${normalizedAppName}-report.html`,
      },
    ],
  ],

};
