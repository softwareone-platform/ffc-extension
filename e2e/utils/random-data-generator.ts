import { v4 as uuidv4 } from 'uuid';

/**
 * Generates a random email address for automated testing purposes that will not bounce.
 * @returns A random, unique email address.
 */
export function generateRandomEmail(): string {
  // Get current timestamp
  const timestamp = Date.now();

  // Generate a random number
  const randomNumber = Math.floor(Math.random() * 1_000);

  // Combine elements into a random email
  return `mpt.qlt+execution-${timestamp}${randomNumber}@gmail.com`;
}

/**
 * Generates a random organization name for automated testing purposes.
 *
 * This function creates a unique organization name by appending a UUID
 * (Universally Unique Identifier) to the base string "Test Organization".
 *
 * @returns {string} A random, unique organization name.
 */
export function generateRandomOrganizationName(): string {
  return `Test Organization ${uuidv4()}`;
}
