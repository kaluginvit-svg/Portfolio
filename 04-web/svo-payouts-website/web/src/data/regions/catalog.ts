/**
 * Каталог региональных выплат — расширяемый источник правды.
 * Суммы и формулировки ниже — демонстрационные/заглушки: при появлении официальных данных
 * замените строки и проставьте sourceUrl / lastUpdated.
 */

export interface RegionalPaymentSpec {
  id: string;
  title: string;
  /** null — сумма не унифицирована или требует проверки */
  amountRub: number | null;
  recipients: string;
  description: string | null;
  note: string | null;
  lastUpdated: string;
  sourceLabel: string;
  sourceUrl: string | null;
  available: boolean;
}

export interface RegionCatalogEntry {
  code: string;
  name: string;
  /** Альтернативные написания для сопоставления с вводом пользователя */
  aliases: string[];
  payments: RegionalPaymentSpec[];
  /** В каталоге только пример; нужна ручная верификация */
  catalogNote: string | null;
}

export const REGIONS_CATALOG: RegionCatalogEntry[] = [
  {
    code: "77",
    name: "Москва",
    aliases: ["москва", "г москва", "г. москва", "мск"],
    catalogNote:
      "Ниже приведены ориентиры для демонстрации интерфейса. Перед опорой на цифры сверьтесь с актуальными нормами Москвы.",
    payments: [
      {
        id: "msk-demo-1",
        title: "Региональная мера поддержки (пример записи)",
        amountRub: null,
        recipients: "Зависит от статуса семьи и основания",
        description:
          "Конкретные меры и размеры в Москве задаются отдельными актами; здесь намеренно без фиксированной суммы.",
        note: "Требуется подбор по документам и году обращения.",
        lastUpdated: "2025-03-01",
        sourceLabel: "Заполните при интеграции с официальным источником",
        sourceUrl: null,
        available: false,
      },
    ],
  },
  {
    code: "78",
    name: "Санкт-Петербург",
    aliases: ["санкт-петербург", "спб", "питер", "с-петербург"],
    catalogNote:
      "Демонстрационная карточка региона. Добавьте проверенные выплаты и ссылки на нормы.",
    payments: [
      {
        id: "spb-demo-1",
        title: "Региональная компенсация (пример с суммой-заглушкой)",
        amountRub: 100_000,
        recipients: "Уточняется по категориям получателей",
        description:
          "Сумма указана как НЕ финальная — только для проверки отображения в интерфейсе.",
        note: "NOT_FINAL — заменить на подтверждённое значение из официального источника.",
        lastUpdated: "2025-03-01",
        sourceLabel: "Placeholder (не для продакшена без замены)",
        sourceUrl: null,
        available: true,
      },
    ],
  },
  {
    code: "00",
    name: "Иной субъект РФ",
    aliases: [],
    catalogNote: null,
    payments: [],
  },
];

/** Нормализация строки региона для сопоставления с каталогом (тестируемая). */
export function normalizeRegionInput(s: string): string {
  return s
    .toLowerCase()
    .trim()
    .replace(/\s+/g, " ")
    .replace(/ё/g, "е");
}

/** Поиск региона по свободному вводу пользователя. */
export function findRegionCatalogEntry(regionInput: string): RegionCatalogEntry | null {
  const q = normalizeRegionInput(regionInput);
  if (q.length < 2) return null;

  let best: RegionCatalogEntry | null = null;
  let bestScore = 0;

  for (const r of REGIONS_CATALOG) {
    if (r.code === "00") continue;
    const candidates = [normalizeRegionInput(r.name), ...r.aliases.map(normalizeRegionInput)];
    for (const c of candidates) {
      if (!c) continue;
      if (q === c) return r;
      if (q.includes(c) || c.includes(q)) {
        const score = Math.min(c.length, q.length);
        if (score > bestScore) {
          bestScore = score;
          best = r;
        }
      }
    }
  }

  return best;
}
