import { existsSync, mkdirSync, readFileSync, statSync, writeFile, writeFileSync } from 'node:fs';
import CryptoJS from 'crypto-js';
import User from './user';
import fs from 'fs';

/**
 * Determines whether a cached Playwright storage state file is still valid.
 *
 * A session file is considered valid when it exists, is non-empty, and was
 * modified within the last 30 minutes.
 *
 * @param {string} filepath - Absolute or relative path to the storage state file.
 * @returns {Promise<boolean>} Resolves to true when the cached session can be reused.
 */
export async function isSessionValid(filepath: string): Promise<boolean> {
  const path = require('path');
  const dirpath = path.dirname(filepath);
  if (!existsSync(dirpath)) mkdirSync(dirpath);
  if (!existsSync(filepath)) {
    writeFileSync(filepath, JSON.stringify({}));
    return false;
  }
  const size = statSync(filepath).size;
  if (size < 3) return false;
  const mtime = statSync(filepath).mtime;
  const thirtyMinutesAgo = new Date(new Date().getTime() - 30 * 60 * 1000);
  // Do NOT wipe the existing session file here. Wiping before fresh login completes
  // creates a race condition: concurrent test workers read an empty storageState and
  // create cookie-less browser contexts that get redirected to the Auth0 login page.
  // Old tokens remain valid well beyond 30 minutes, so leaving them in place is safe.
  return mtime >= thirtyMinutesAgo;
}

/**
 * Encrypts and stores a secret value on disk.
 *
 * @param {string} filepath - Destination file path for the encrypted value.
 * @param {string} secret - Plaintext secret to encrypt and persist.
 * @param {string} unlockKey - Key used to encrypt the secret.
 * @returns {Promise<void>} Resolves after the write operation is scheduled.
 */
export async function storeSecretToFile(filepath: string, secret: string, unlockKey: string): Promise<void> {
  const encrypted: string = CryptoJS.AES.encrypt(secret, unlockKey).toString();
  writeFile(filepath, encrypted, function (err) {
    if (err) {
      console.warn(`Warning:${err}`);
    }
  });
}

/**
 * Reads and decrypts a previously stored secret from disk.
 *
 * @param {string} filepath - File path that contains the encrypted secret.
 * @param {string} unlockKey - Key used to decrypt the secret.
 * @returns {string} Decrypted secret, or an empty string when the file does not exist.
 */
export function getSecretFromFile(filepath: string, unlockKey: string): string {
  if (!existsSync(filepath)) return '';
  return CryptoJS.AES.decrypt(readFileSync(filepath, 'utf-8'), unlockKey).toString(CryptoJS.enc.Utf8);
}

/**
 * Invalidates cached user session files for the provided list of users.
 * This ensures that fresh login sessions are created for the users.
 *
 * @param {User[]} users - An array of user objects whose session caches need to be invalidated.
 */
export function invalidateUserSessionCache(users: User[]): void {
  for (const user of users) {
    try {
      const sessionPath = user.sessionStoragePath;
      if (fs.existsSync(sessionPath)) {
        fs.rmSync(sessionPath, { force: true });
        console.log(`Invalidated cached session: ${sessionPath}`);
      }
    } catch (error) {
      console.error(`Failed to invalidate cached session for ${user.email}:`, error);
    }
  }
}
