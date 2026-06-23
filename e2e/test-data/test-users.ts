import User from '../utils/user';
import {getCurrentEnv} from "../utils/utils";

/**
 * Returns the value of a required environment variable.
 *
 * @param name - The environment variable name to read from `process.env`.
 * @returns The environment variable value when it is defined and non-empty.
 * @throws {Error} Throws when the variable is missing or empty.
 */
const requireEnv = (name: string): string => {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }

  return value;
};

export default class TestUsers {
  static readonly Admin = new User('mpt.qlt+ffc-admin@gmail.com', requireEnv('DEFAULT_USER_PASSWORD'), 'FFC Admin', 'Vendor');
}
