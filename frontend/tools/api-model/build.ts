import { exec } from 'child_process';
import { existsSync, mkdirSync, readFileSync, renameSync, rmSync, writeFileSync } from 'fs';
import path from 'path';
import { exit } from 'process';

// import util from 'util';
// const execP = util.promisify(exec);

const models = [{
  displayName: 'FFC Extension API Model',
  apiName: 'ffc-api-model',
  name: 'ffc-api-model',
  file: 'ffc-api-model.json'
}];

async function run() {
  const source = path.resolve('./tools/api-model');
  const rootDestination = path.resolve(`./src/api/`);

  for (const swagger of models) {
    const destination = path.resolve(rootDestination, `./${swagger.name}`);
    if (existsSync(destination)) {
      rmSync(destination, { recursive: true });
    }

    mkdirSync(destination, { recursive: true });

    console.log(`[ffc-api-model][${swagger.displayName}] Cleaning up swagger`);
    const swaggerFilePath = path.resolve(source, 'swagger', swagger.file);
    const swaggerFileData = readFileSync(swaggerFilePath).toString('utf-8');
    // Removes string patterns as openapi typescript template doesn't support it
    writeFileSync(swaggerFilePath, swaggerFileData.replace(/,\s*"allOf":\s*\[(\s*\{\s*"pattern":\s*[^\]]*)]/gm, ''));
    console.log(`[ffc-api-model][${swagger.displayName}] Cleaned up swagger`);

    const execSCript = `npm run generate-model -- --input ${swaggerFilePath} --output ${destination}`;
    console.log(`[ffc-api-model][${swagger.displayName}] Generating model: ${execSCript}`);
    await new Promise<void>(res => exec(execSCript, () => res()));
    console.log(`[ffc-api-model][${swagger.displayName}] Generated model`);

    await new Promise<void>((res, rej) => {
      console.log(`[ffc-api-model][${swagger.displayName}] Checking for generated model files`);
      const intervalId = setInterval(() => {
        if (existsSync(destination + '/index.ts')) {
          res();
        }
      }, 100);

      setTimeout(() => {
        clearInterval(intervalId);
        rej('File ' + (destination + '/index.ts') + ' not found before timeout');
      }, 1000);
    });

    console.log(`[ffc-api-model][${swagger.displayName}] Copying files to ${destination}`);

    renameSync(destination + '/index.ts', destination + '/index.d.ts');
    console.log(`[ffc-api-model][${swagger.displayName}] Copied files`);
    console.log(`[ffc-api-model][${swagger.displayName}] Build successful`);
  }

  exit(0);
}

run();
