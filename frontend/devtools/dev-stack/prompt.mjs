// Console prompting, including the non-interactive path. A pipe delivers every line at once and
// readline drops the ones no question() awaits, so scripted input is drained up front — that also
// makes the picker usable from a script or a test.
import { createInterface } from "node:readline";
import process from "node:process";

const interactive = process.stdin.isTTY;

const scripted = interactive
  ? []
  : (
      await new Promise((resolveInput) => {
        let buffer = "";
        process.stdin.setEncoding("utf8");
        process.stdin.on("data", (chunk) => (buffer += chunk));
        process.stdin.on("end", () => resolveInput(buffer));
      })
    )
      .split("\n")
      .map((line) => line.trim());

export const ask = async (question) => {
  if (!interactive) {
    // Refusing to invent answers matters now that the picker loops: a script that runs out of
    // input would otherwise keep taking the default choice forever.
    if (scripted.length === 0) {
      console.log(question);
      console.error("\n!  Out of scripted input.");
      process.exit(1);
    }
    const answer = scripted.shift();
    console.log(`${question}${answer}`);
    return answer;
  }

  // Opened per question and closed straight after, so no interface is holding stdin while a
  // spawned task has the terminal.
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  try {
    return await new Promise((resolvePrompt) =>
      rl.question(question, (answer) => resolvePrompt(answer.trim())),
    );
  } finally {
    rl.close();
  }
};

export async function choose(title, options) {
  console.log(`\n${title}`);
  options.forEach((option, index) => console.log(`  ${index + 1}) ${option.label}`));

  const answer = await ask(`Select [1-${options.length}] (default 1): `);
  const index = answer === "" ? 0 : Number(answer) - 1;
  if (!Number.isInteger(index) || index < 0 || index >= options.length) {
    console.error(`\nNot a valid choice: "${answer}"`);
    process.exit(1);
  }
  return options[index].value;
}

export const pad = (text, width) => text.padEnd(width);
