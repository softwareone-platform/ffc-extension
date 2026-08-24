import * as fs from 'fs';
import * as path from 'path';

/** Creates the directory (and parents) if it does not already exist. */
export function ensureDir(dirPath: string): void {
  fs.mkdirSync(dirPath, { recursive: true });
}

/** Returns the parsed JSON, or `undefined` when the file is missing or unreadable. */
export function safeReadJsonFile<T>(filePath: string): T | undefined {
  try {
    if (!fs.existsSync(filePath)) return undefined;
    const raw = fs.readFileSync(filePath, 'utf-8');
    if (raw.trim().length === 0) return undefined;
    return JSON.parse(raw) as T;
  } catch {
    return undefined;
  }
}

/**
 * Writes JSON synchronously and verifies it landed. Synchronous on purpose: the
 * previous callback-based write resolved before the file existed, so readers
 * (and concurrent workers) could observe a missing or empty file.
 */
export function safeWriteJsonFile(filePath: string, data: unknown): void {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');

  if (!fs.existsSync(filePath)) {
    throw new Error(`Failed to write file: ${filePath}`);
  }
}

/** Milliseconds since the file was last modified, or `undefined` when missing. */
export function fileAgeMs(filePath: string): number | undefined {
  try {
    return Date.now() - fs.statSync(filePath).mtimeMs;
  } catch {
    return undefined;
  }
}
