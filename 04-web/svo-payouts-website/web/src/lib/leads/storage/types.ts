import type { StoredLeadRecord } from "@/types/stored-lead";

/** Абстракция хранилища лидов — позже можно подставить БД без смены API-роута. */
export interface LeadsStorage {
  save(lead: StoredLeadRecord): Promise<StoredLeadRecord>;
  /** Точечное обновление записи (например, флаг Telegram после отправки). */
  patchLead(id: string, patch: Partial<StoredLeadRecord>): Promise<void>;
}
