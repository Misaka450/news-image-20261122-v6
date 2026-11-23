import { copyFileSync, existsSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const outputDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
// Ensure the output directory exists (defaults to /output, overridable via MAKEFUN_OUTPUT_DIR)
mkdirSync(outputDir, { recursive: true });
const srcPath = join(import.meta.dirname, 'entry.png');
if (!existsSync(srcPath)) {
  throw new Error(`Source file not found: ${srcPath}`);
}
const destPath = join(outputDir, 'entry.png');
copyFileSync(srcPath, destPath);
console.log(destPath);
