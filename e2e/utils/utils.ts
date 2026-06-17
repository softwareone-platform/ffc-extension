/* eslint-disable @typescript-eslint/no-non-null-assertion */
/* eslint-disable @typescript-eslint/no-var-requires */
import { existsSync, mkdirSync, readFileSync, statSync, writeFile, writeFileSync } from 'fs';

import CryptoJS from 'crypto-js';
import { testEnvironmentData } from '../test-data/env-data/testEnvironmentData';
import { TestData } from '../types/TestData';
import { debugLog } from './debug-logging';
import { devEnvironmentData } from '../test-data/env-data/devEnvironmentData';


/**
 * Reads a variable from process.env (or npm_config_), then falls back to
 * an environment-suffixed key like VARIABLE_TEST.
 */
export function readEnvironmentVariable(variableName: string): string {
  let secretValue = process.env[variableName.toUpperCase()] || process.env['npm_config_' + variableName.toUpperCase()];

  //fallback to variables with environment
  if (secretValue == null) {
    const variableNameWithEnv = (variableName + '_' + getCurrentEnv().name).toUpperCase();
    console.warn('Warning: Variable', variableName, 'not found, trying to read variable:', variableNameWithEnv);
    // eslint-disable-next-line @typescript-eslint/strict-boolean-expressions
    secretValue = process.env[variableNameWithEnv] || process.env['npm_config_' + variableNameWithEnv];
  }

  if (secretValue == null) {
    console.warn('Warning: Unable to read environment variable:' + variableName);
    secretValue = '';
  }
  return secretValue;
}

/** Encrypts a secret and stores it on disk using the provided unlock key. */
export async function storeSecretToFile(filepath: string, secret: string, unlockKey: string): Promise<void> {
  const encrypted: string = CryptoJS.AES.encrypt(secret, unlockKey).toString();
  writeFile(filepath, encrypted, function (err) {
    if (err) {
      console.warn(`Warning:${err}`);
    }
  });
}

/** Reads and decrypts a secret from disk; returns an empty string when the file is missing. */
export function getSecretFromFile(filepath: string, unlockKey: string): string {
  if (!existsSync(filepath)) return '';
  return CryptoJS.AES.decrypt(readFileSync(filepath, 'utf-8'), unlockKey).toString(CryptoJS.enc.Utf8);
}

/** Waits until a token file exists or the timeout is reached. */
export async function waitForToken(filepath: string, maxTimeout: number = 1000): Promise<boolean> {
  const startTime = Date.now();
  while (!existsSync(filepath) && Date.now() - startTime < maxTimeout) {
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  return true;
}

/**
 * Validates that a saved Playwright session file exists, is non-empty, and is fresh.
 * Freshness currently means the file was modified in the last 30 minutes.
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

/** Returns environment-specific test data based on ENVIRONMENT; defaults to TEST. */
export function getCurrentEnv(): TestData {
  const env = process.env['ENVIRONMENT']?.toUpperCase() ?? 'TEST';

  switch (env) {
    case 'TEST':
      return testEnvironmentData;
    case 'DEV':
      return devEnvironmentData;
    default:
      return testEnvironmentData;
  }
}

/** Safely resolves a nested value from an object by traversing the given path. */
export function getNestedValue(obj: unknown, path: string[]): unknown {
  return path.reduce((acc, key) => acc?.[key], obj);
}

/** Truncates a string and appends ellipsis when it exceeds maxLength. */
export function limitString(inputStr: string, maxLength: number): string {
  return inputStr.length > maxLength ? inputStr.substring(0, maxLength) + '...' : inputStr;
}

/** Converts a string to sentence-style casing (first letter uppercase, rest lowercase). */
export function uppercaseFirstLowercaseRest(input: string): string {
  if (input.length === 0) {
    return input;
  }

  return input.charAt(0).toUpperCase() + input.slice(1).toLowerCase();
}

/**
 * Reads a property from an object and returns a fallback when the object is invalid
 * or the key is missing.
 */
export function getPropertyFromObjectOrDefault(obj, key, def?) {
  try {
    if (key in obj) {
      return obj[key];
    }
  } catch (error) {
    if (def === undefined) def = '';
    if (error instanceof TypeError) {
      debugLog(`object does not have field "${key}": ${obj}`);
      return def;
    } else {
      console.error('Error:', error.message);
    }
  }
}

/** Left-pads a number with zero when needed (e.g. 3 -> 03). */
export function padTo2Digits(num: number): string {
  return num.toString().padStart(2, '0');
}

/** Formats a date as YYYY-MM-DD. */
export function formatDateToYmd(date: Date): string {
  return [date.getFullYear(), padTo2Digits(date.getMonth() + 1), padTo2Digits(date.getDate())].join('-');
}

/** Formats a date as HH:mm:ss in local time. */
export function formatDateToHms(date: Date): string {
  return [padTo2Digits(date.getHours()), padTo2Digits(date.getMinutes()), padTo2Digits(date.getSeconds())].join(':');
}

/** Formats a date as `D Mon YYYY` using the provided locale for month names. */
export function formatDateAsDayMonthYear(date: Date, locale: string = 'en-US'): string {
  const day = date.getDate();
  const month = date.toLocaleString(locale, { month: 'short' });
  const year = date.getFullYear();
  return `${day} ${month} ${year}`;
}

/** Formats a date as `YYYY-MM-DD HH:mm:ss`. */
export function formatDateToYmdHms(date: Date): string {
  return `${formatDateToYmd(date)} ${formatDateToHms(date)}`;
}

/** Returns a copy of the date shifted by one calendar year. */
export function getNextYearSameDate(date: Date): Date {
  const nextYearDate = new Date(date);
  nextYearDate.setFullYear(date.getFullYear() + 1);
  return nextYearDate;
}

/** Returns a copy of the date shifted by the provided number of days. */
export function getDateInSomeDays(date: Date, days: number): Date {
  const newDate = new Date(date);
  newDate.setDate(newDate.getDate() + days);
  return newDate;
}

/** Returns a copy of the date shifted forward by one calendar month. */
export function getDatePlusOneMonth(date: Date): Date {
  const nextMonthDate = new Date(date);
  nextMonthDate.setMonth(nextMonthDate.getMonth() + 1);
  return nextMonthDate;
}

/** Converts a number to a fixed decimal string. */
export function padDecimals(value: number, decimalPlaces: number = 5): string {
  return value.toFixed(decimalPlaces);
}

/** Rounds a number to a fixed number of decimal places. */
export function roundToDecimals(value: number, decimals: number = 2): number {
  return parseFloat(padDecimals(value, decimals));
}

/** Returns a random integer within the inclusive [min, max] range. */
export function getRandomNumber(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/** Builds a random lowercase alphanumeric string of the requested length. */
export function getRandomAlphanumeric(length: number = 10): string {
  const characters = 'abcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    const randomIndex = Math.floor(Math.random() * characters.length);
    result += characters[randomIndex];
  }
  return result;
}

/** Returns a random number in range, clamped to be non-negative. */
export function getRandomPositiveNumber(min: number, max: number): number {
  return Math.max(0, getRandomNumber(min, max));
}

/** Expands an array to a target size by appending a default string value. */
export function fillArrayWithEmptyStrings(arr: string[], num: number, value: string = ''): string[] {
  const newArray = [...arr];
  while (newArray.length < num) {
    newArray.push(value);
  }
  return newArray;
}

/** Formats a number with thousands separators. */
export function formatNumberWithCommas(num: number): string {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/** Minimal shape used when surfacing test failures in helpers. */
export interface TestError {
  name: string;
  message: string;
}
