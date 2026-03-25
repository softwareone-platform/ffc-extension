import { EDatasourceType } from '../types/enums';

/**
 * Checks if a given string is a valid value from the EDatasourceType enum.
 *
 * @param {string} value - The string to check.
 * @returns {value is EDatasourceType} - Returns true if the string is a valid EDatasourceType value, otherwise false.
 */
export function isDatasourceType(value: string): value is EDatasourceType {
  return Object.values(EDatasourceType).includes(value as EDatasourceType);
}
