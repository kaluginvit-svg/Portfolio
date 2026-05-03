import { describe, expect, it } from "vitest";
import {
  findRegionCatalogEntry,
  normalizeRegionInput,
} from "@/data/regions/catalog";

describe("normalizeRegionInput", () => {
  it("регистр, пробелы, ё→е", () => {
    expect(normalizeRegionInput("  Москва  ")).toBe("москва");
    expect(normalizeRegionInput("Екатеринбург")).toBe("екатеринбург");
  });
});

describe("findRegionCatalogEntry", () => {
  it("точное совпадение с названием", () => {
    const e = findRegionCatalogEntry("Москва");
    expect(e?.code).toBe("77");
    expect(e?.name).toBe("Москва");
  });

  it("алиас мск", () => {
    expect(findRegionCatalogEntry("мск")?.code).toBe("77");
  });

  it("Санкт-Петербург и спб", () => {
    expect(findRegionCatalogEntry("Санкт-Петербург")?.code).toBe("78");
    expect(findRegionCatalogEntry("спб")?.code).toBe("78");
  });

  it("подстрока в запросе (нормализованный ввод содержит название)", () => {
    expect(findRegionCatalogEntry("Москва и область")?.code).toBe("77");
  });

  it("короче 2 символов → null", () => {
    expect(findRegionCatalogEntry("а")).toBeNull();
    expect(findRegionCatalogEntry(" ")).toBeNull();
  });

  it("неизвестный регион: лучший частичный или null", () => {
    const ghost = findRegionCatalogEntry("Несуществующая область XYZ");
    expect(ghost).toBeNull();
  });
});
