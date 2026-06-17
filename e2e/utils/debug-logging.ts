import { formatDateToYmdHms, limitString } from './utils';

/**
 * Logs a debug message to the console if debugging is enabled.
 *
 * This function checks the `DEBUG_LOG` environment variable to determine
 * if debug logging is enabled. If it is set to 'true', the provided message
 * is logged to the console with a `[DEBUG]` prefix.
 *
 * @param {string} message - The debug message to log.
 * @param messageType
 */
export function debugLog(message: string, messageType: string = 'debug'): void {
  process.env['DEBUG'] = 'true';
  const trueValues = ['true', true];
  const debugValue = process.env['DEBUG'] ?? 'false';

  if (trueValues.includes(debugValue)) {
    console.log(`${formatDateToYmdHms(new Date())} [${limitString(messageType.toUpperCase(), 10)}]: ${message}`);
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
