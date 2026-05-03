import { mkdir, readFile, writeFile } from "fs/promises";
import path from "path";
import type { StoredLeadRecord } from "@/types/stored-lead";
import type { LeadsStorage } from "@/lib/leads/storage/types";

let writeChain: Promise<void> = Promise.resolve();

function resolvePath(filePath: string): string {
  return path.isAbsolute(filePath)
    ? filePath
    : path.join(process.cwd(), filePath);
}

export class FileLeadsStorage implements LeadsStorage {
  constructor(private readonly filePath: string) {}

  async save(lead: StoredLeadRecord): Promise<StoredLeadRecord> {
    const abs = resolvePath(this.filePath);
    const dir = path.dirname(abs);

    await mkdir(dir, { recursive: true });

    const run = async () => {
      let list: StoredLeadRecord[] = [];
      try {
        const raw = await readFile(abs, "utf8");
        const parsed = JSON.parse(raw) as unknown;
        if (Array.isArray(parsed)) list = parsed as StoredLeadRecord[];
      } catch {
        /* файл отсутствует или битый — начинаем с пустого массива */
      }
      list.push(lead);
      await writeFile(abs, JSON.stringify(list, null, 2), "utf8");
    };

    writeChain = writeChain.then(run, run);
    await writeChain;
    return lead;
  }

  async patchLead(id: string, patch: Partial<StoredLeadRecord>): Promise<void> {
    const abs = resolvePath(this.filePath);
    const dir = path.dirname(abs);

    const run = async () => {
      await mkdir(dir, { recursive: true });
      let list: StoredLeadRecord[] = [];
      try {
        const raw = await readFile(abs, "utf8");
        const parsed = JSON.parse(raw) as unknown;
        if (Array.isArray(parsed)) list = parsed as StoredLeadRecord[];
      } catch {
        return;
      }
      const i = list.findIndex((l) => l.id === id);
      if (i < 0) return;
      list[i] = { ...list[i], ...patch };
      await writeFile(abs, JSON.stringify(list, null, 2), "utf8");
    };

    writeChain = writeChain.then(run, run);
    await writeChain;
  }
}
