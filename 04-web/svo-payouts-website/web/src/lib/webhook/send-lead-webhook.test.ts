import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { sendLeadWebhook } from "@/lib/webhook/send-lead-webhook";
import type { StoredLeadRecord } from "@/types/stored-lead";

const sampleLead: StoredLeadRecord = {
  id: "550e8400-e29b-41d4-a716-446655440000",
  createdAt: "2025-06-01T12:00:00.000Z",
  flowMode: "fresh",
  scenario: "A",
  statusOfDeceased: "мобилизованный",
  applicantRole: "супруг(а)",
  complexStatus: null,
  recipientsCount: 1,
  documentsOnHand: "свидетельство о смерти",
  problemType: null,
  submittedTo: null,
  monthsWaiting: null,
  stuckSummary: null,
  region: "Москва",
  baseTotal: 1000,
  personalShare: 1000,
  estimatedDelayLoss: 0,
  name: "Иван",
  phone: "+79001234567",
  phoneRaw: "89001234567",
  messenger: null,
  email: "a@b.ru",
  comment: null,
  consentAccepted: true,
  utm_source: null,
  utm_medium: null,
  utm_campaign: null,
  telegramSent: false,
};

describe("sendLeadWebhook", () => {
  const origUrl = process.env.LEAD_WEBHOOK_URL;
  const origSecret = process.env.LEAD_WEBHOOK_SECRET;

  beforeEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    delete process.env.LEAD_WEBHOOK_URL;
    delete process.env.LEAD_WEBHOOK_SECRET;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    if (origUrl === undefined) delete process.env.LEAD_WEBHOOK_URL;
    else process.env.LEAD_WEBHOOK_URL = origUrl;
    if (origSecret === undefined) delete process.env.LEAD_WEBHOOK_SECRET;
    else process.env.LEAD_WEBHOOK_SECRET = origSecret;
  });

  it("без URL — пропуск", async () => {
    const r = await sendLeadWebhook(sampleLead);
    expect(r).toEqual({ ok: false, skipped: true, reason: "no_config" });
  });

  it("отправляет POST с телом event + lead", async () => {
    process.env.LEAD_WEBHOOK_URL = "https://hooks.example.com/lead";

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () => "",
    });
    vi.stubGlobal("fetch", fetchMock);

    const r = await sendLeadWebhook(sampleLead);
    expect(r).toEqual({ ok: true });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [calledUrl, init] = fetchMock.mock.calls[0] as [
      string,
      RequestInit,
    ];
    expect(calledUrl).toBe("https://hooks.example.com/lead");
    expect(init.method).toBe("POST");
    const headers = init.headers as Record<string, string>;
    expect(headers["Content-Type"]).toBe("application/json");
    expect(headers.Authorization).toBeUndefined();
    const parsed = JSON.parse(init.body as string) as {
      event: string;
      lead: StoredLeadRecord;
    };
    expect(parsed.event).toBe("lead.created");
    expect(parsed.lead.id).toBe(sampleLead.id);
  });

  it("добавляет Bearer при LEAD_WEBHOOK_SECRET", async () => {
    process.env.LEAD_WEBHOOK_URL = "https://hooks.example.com/lead";
    process.env.LEAD_WEBHOOK_SECRET = "secret-token";

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () => "",
    });
    vi.stubGlobal("fetch", fetchMock);

    await sendLeadWebhook(sampleLead);

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = init.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer secret-token");
  });
});
