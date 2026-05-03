import { expect, test } from "@playwright/test";

test.describe("Навигация квиза", () => {
  test("Назад: возврат на предыдущий шаг", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Узнать, какие выплаты положены" }).first().click();
    await page.getByRole("button", { name: "Был мобилизован" }).click();
    await page.getByRole("button", { name: "Супруг или супруга" }).click();

    await page.getByRole("button", { name: "Назад" }).click();

    await expect(
      page.getByRole("heading", { name: /Кем вы ему приходитесь/i }),
    ).toBeVisible();
  });

  test("Очистить расчёт: сброс после подтверждения", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Узнать, какие выплаты положены" }).first().click();
    await page.getByRole("button", { name: "Был мобилизован" }).click();

    page.once("dialog", (d) => d.accept());
    await page.getByRole("button", { name: "Очистить расчёт" }).click();

    await expect(page.getByRole("heading", { name: /С чего начнём/i })).toBeVisible();
  });

  test("localStorage: черновик после перезагрузки", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Узнать, какие выплаты положены" }).first().click();
    await page.getByRole("button", { name: "Был мобилизован" }).click();
    await page.getByRole("button", { name: "Супруг или супруга" }).click();

    await page.reload();

    await expect(page.getByText(/Шаг 3 из/)).toBeVisible({ timeout: 10_000 });
  });
});

test.describe("Статические страницы", () => {
  test("/privacy и /consent открываются", async ({ page }) => {
    await page.goto("/privacy");
    await expect(page.getByRole("heading", { level: 1 })).toContainText(/политик/i);

    await page.goto("/consent");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  });
});
