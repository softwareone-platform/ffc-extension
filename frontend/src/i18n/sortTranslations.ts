import fs from "fs";
// const { glob } = require("glob");
import { glob } from "glob";

const TRANSLATION_PATH = "src/i18n/**/*.json";

(async function sortTranslations() {
  const files = await glob(TRANSLATION_PATH);

  files.forEach((file) => {
    try {
      const content = fs.readFileSync(file, { encoding: "utf8" });
      const parsedContent = JSON.parse(content);

      const output = Object.keys(parsedContent)
        .sort((a, b) => a.localeCompare(b))
        .reduce((result, key) => ({ ...result, [key]: parsedContent[key] }), {});

      fs.writeFileSync(file, JSON.stringify(output));
    } catch (error) {
      console.log(error);
    }
  });
})();
