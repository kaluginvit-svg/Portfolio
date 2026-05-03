import { FileLeadsStorage } from "@/lib/leads/storage/file-storage";
import { MemoryLeadsStorage } from "@/lib/leads/storage/memory-storage";
import type { LeadsStorage } from "@/lib/leads/storage/types";

const DEFAULT_FILE = "./data/leads.json";

let cached: LeadsStorage | null = null;

export function getLeadsStorage(): LeadsStorage {
  if (cached) return cached;

  const mode = (
    process.env.LEADS_STORAGE_MODE ??
    process.env.STORAGE_MODE ??
    "file"
  )
    .toLowerCase()
    .trim();

  if (mode === "memory") {
    cached = new MemoryLeadsStorage();
    return cached;
  }

  const filePath = process.env.LEADS_FILE_PATH?.trim() || DEFAULT_FILE;
  cached = new FileLeadsStorage(filePath);
  return cached;
}

/** Сброс кэша (тесты / hot reload в dev) */
export function resetLeadsStorageCache(): void {
  cached = null;
}
