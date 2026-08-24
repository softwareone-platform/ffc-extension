import { env } from './env';
import { formatDateToYmdHms, limitString } from './format';

export function debugLog(message: string, messageType: string = 'debug'): void {
  if (!env.debugLog) return;

  console.log(`${formatDateToYmdHms(new Date())} [${limitString(messageType.toUpperCase(), 10)}]: ${message}`);
}

export function errorLog(message: string): void {
  console.error(`[ERROR] ${message}`);
}
