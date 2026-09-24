import * as fs from 'fs';
import * as path from 'path';

export function ensureDir(dirPath: string): void {
  fs.mkdirSync(dirPath, { recursive: true });
}

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

/** Sync and verified: the previous callback write resolved before the file existed. */
export function safeWriteJsonFile(filePath: string, data: unknown): void {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');

  if (!fs.existsSync(filePath)) {
    throw new Error(`Failed to write file: ${filePath}`);
  }
}
