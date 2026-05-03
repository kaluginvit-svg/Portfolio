import { describe, expect, it, afterEach } from "vitest";
import { resolveSiteUrl } from "@/lib/site-url";

describe("resolveSiteUrl", () => {
  const orig = process.env.NEXT_PUBLIC_SITE_URL;

  afterEach(() => {
    if (orig === undefined) delete process.env.NEXT_PUBLIC_SITE_URL;
    else process.env.NEXT_PUBLIC_SITE_URL = orig;
  });

  it("без env — localhost", () => {
    delete process.env.NEXT_PUBLIC_SITE_URL;
    expect(resolveSiteUrl()).toBe("http://localhost:3000");
  });

  it("добавляет https без схемы", () => {
    process.env.NEXT_PUBLIC_SITE_URL = "example.ru";
    expect(resolveSiteUrl()).toBe("https://example.ru");
  });

  it("убирает завершающий слэш", () => {
    process.env.NEXT_PUBLIC_SITE_URL = "https://svo.example.ru/";
    expect(resolveSiteUrl()).toBe("https://svo.example.ru");
  });
});
