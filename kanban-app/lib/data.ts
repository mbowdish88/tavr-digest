import { readFileSync, writeFileSync, existsSync } from "fs";
import { join } from "path";

const DATA_DIR = join(process.cwd(), "data");

function ensureFile(filename: string, defaultData: unknown): void {
  const path = join(DATA_DIR, filename);
  if (!existsSync(path)) {
    writeFileSync(path, JSON.stringify(defaultData, null, 2));
  }
}

export function readJson<T>(filename: string, defaultData: T): T {
  ensureFile(filename, defaultData);
  const path = join(DATA_DIR, filename);
  const raw = readFileSync(path, "utf-8");
  return JSON.parse(raw) as T;
}

export function writeJson<T>(filename: string, data: T): void {
  const path = join(DATA_DIR, filename);
  writeFileSync(path, JSON.stringify(data, null, 2));
}
