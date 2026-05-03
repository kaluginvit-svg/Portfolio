import type { StoredLeadRecord } from "@/types/stored-lead";
import type { LeadsStorage } from "@/lib/leads/storage/types";

const leads: StoredLeadRecord[] = [];

export class MemoryLeadsStorage implements LeadsStorage {
  async save(lead: StoredLeadRecord): Promise<StoredLeadRecord> {
    leads.push(lead);
    return lead;
  }

  async patchLead(id: string, patch: Partial<StoredLeadRecord>): Promise<void> {
    const i = leads.findIndex((l) => l.id === id);
    if (i < 0) return;
    leads[i] = { ...leads[i], ...patch };
  }
}

/** Для отладки / тестов */
export function __memoryLeadsSnapshot(): readonly StoredLeadRecord[] {
  return leads;
}
