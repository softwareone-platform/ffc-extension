import * as dotenv from 'dotenv';
import * as fs from 'fs';
import * as path from 'path';

export function loadEnvVariables(env: string) {
  const envPath = path.resolve(__dirname, '..', `.env.${env}`);
  if (!fs.existsSync(envPath)) {
    throw new Error(`Environment file for '${env}' not found at ${envPath}`);
  }
  dotenv.config({ path: envPath });
  // Avoid importing utility modules here because they read env-dependent data at import time.
  console.log(`Loaded environment variables from ${envPath}`);
}
