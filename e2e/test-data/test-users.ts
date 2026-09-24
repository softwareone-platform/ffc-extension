import { env } from '../utils/env';
import User from '../utils/user';

// Importing env guarantees the .env files are loaded before this static field runs.
// A missing password is reported by requireEnv() in setup/auth.setup.ts.
export default class TestUsers {
  static readonly Admin = new User('mpt.qlt+ffc-admin@gmail.com', env.defaultUserPassword, 'FFC Admin', 'Vendor');
}
