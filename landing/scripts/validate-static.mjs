import { readFile, stat } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join, resolve } from "node:path";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));

async function requireFile(path) {
  const target = join(root, path);
  const info = await stat(target);

  if (!info.isFile()) {
    throw new Error(`${path} is not a file`);
  }

  return readFile(target, "utf8");
}

function assertIncludes(content, needle, label) {
  if (!content.includes(needle)) {
    throw new Error(`${label} is missing required content: ${needle}`);
  }
}

const html = await requireFile("index.html");
await requireFile("styles.css");
await requireFile("app.js");

assertIncludes(html, "<title>", "index.html");
assertIncludes(html, "styles.css", "index.html");
assertIncludes(html, "app.js", "index.html");
assertIncludes(html, "local-first", "index.html");
assertIncludes(html, "evidence", "index.html");
assertIncludes(html, "supervisada", "index.html");

console.log("QuantLab landing static validation passed.");
