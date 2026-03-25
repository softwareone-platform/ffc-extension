/**
 * Logs a debug message to the console if debugging is enabled.
 *
 * This function checks the `DEBUG_LOG` environment variable to determine
 * if debug logging is enabled. If it is set to 'true', the provided message
 * is logged to the console with a `[DEBUG]` prefix.
 *
 * @param {string} message - The debug message to log.
 */
export function debugLog(message: string) {
  if (process.env.DEBUG_LOG === 'true') {
    console.debug(`[DEBUG] ${message}`);
  }
}
/**
 * Logs an error message to the console.
 *
 * This function prefixes the provided message with `[ERROR]` and logs it
 * to the console using `console.error`.
 *
 * @param {string} message - The error message to log.
 */
export function errorLog(message: string) {
  console.error(`[ERROR] ${message}`);
}
