import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const sourcePath = path.join(here, '..', 'src', 'main.ts');
const source = await readFile(sourcePath, 'utf8');

for (const forbidden of [
  '.modify(', '.process(', 'processFrontMatter(', '.create(', '.delete(', '.rename(',
]) {
  assert.equal(source.includes(forbidden), false, `write API forbidden in read-only plugin: ${forbidden}`);
}

assert.match(source, /cachedRead\(/);
assert.match(source, /metadataCache/);
assert.match(source, /openLinkText\(/);
assert.match(source, /projectionAuthority/);
console.log('read-only contract PASS');
