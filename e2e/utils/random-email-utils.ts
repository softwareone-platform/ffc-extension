/**
 * Generates a random email address for automated testing purposes that will not bounce.
 * @returns A random, unique email address.
 */
export function generateRandomEmail(): string {
  // Get current timestamp
  const timestamp = Date.now();

  // Generate a random number
  const randomNumber = Math.floor(Math.random() * 100);

  // Combine elements into a random email
  return `mpt.qlt+ffc-${timestamp}${randomNumber}@gmail.com`;
}
