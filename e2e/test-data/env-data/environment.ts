import { TestData } from '../../types/TestData';
import {testEnvironmentData} from "./testEnvironmentData";
import {devEnvironmentData} from "./devEnvironmentData";

const DATA = {
  DEV: devEnvironmentData as TestData,
  TEST: testEnvironmentData as TestData,
};

interface Data {
  [name: string]: TestData;
}

/**
 * Returns the active test environment key.
 * Defaults to TEST when ENVIRONMENT is not set.
 */
export function getEnvironment() {
  const env = process.env['ENVIRONMENT'] ?? 'TEST';
  return env.toUpperCase();
}

/**
 * Resolves the environment-specific test data object.
 */
export default function getTestData(): TestData {
  return (DATA as Data)[getEnvironment()];
}
