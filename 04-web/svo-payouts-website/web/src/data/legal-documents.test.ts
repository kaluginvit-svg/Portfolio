import { describe, expect, it } from "vitest";
import {
  legalDocuments,
  legalDownloadFilenames,
  legalDownloadHref,
} from "@/data/legal-documents";

describe("legalDownloadHref", () => {
  it("указывает на .docx в /legal/ с именами из public/legal", () => {
    for (const id of ["privacy", "consent"] as const) {
      const name = legalDownloadFilenames[id];
      const path = legalDownloadHref[id];
      expect(path.startsWith("/legal/")).toBe(true);
      expect(
        decodeURIComponent(path.slice("/legal/".length)),
      ).toBe(name);
    }
  });

  it("у каждого документа есть абзацы для страницы", () => {
    expect(legalDocuments.privacy.paragraphs.length).toBeGreaterThan(0);
    expect(legalDocuments.consent.paragraphs.length).toBeGreaterThan(0);
  });
});
