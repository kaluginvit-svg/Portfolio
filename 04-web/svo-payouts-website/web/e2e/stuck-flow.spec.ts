import { expect, test } from "@playwright/test";

test.describe("Stuck / clarify flow → расчёт", () => {
  test("clarify 7 шагов → кнопка расчёта → результат", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("button", { name: "Прояснить ситуацию" }).first().click();

    await page.getByRole("button", { name: /свидетельство о смерти уже на руках/i }).click();
    await page
      .getByRole("button", { name: /Да, есть извещение или справка из части/i })
      .click();
    await page
      .getByRole("button", { name: /пакет по родству в полном объёме/i })
      .click();
    await page.getByRole("button", { name: /Копии заверены или готовы к подаче/i }).click();
    await page.getByRole("button", { name: /Подали комплект и ждём ответа/i }).click();
    await page.getByRole("button", { name: /В СФР или МФЦ/i }).click();
    await page.getByRole("button", { name: /Общая картина/i }).click();

    await expect(page.locator("#clarify-thanks")).toBeVisible({ timeout: 15_000 });

    await page
      .locator("#clarify-thanks")
      .getByRole("button", { name: "Узнать, какие выплаты положены" })
      .click();

    await page.getByRole("button", { name: "Был мобилизован" }).click();
    await page.getByRole("button", { name: "Супруг или супруга" }).click();
    await page.getByRole("button", { name: "Только я" }).click();
    await page.getByRole("checkbox", { name: "Свидетельство о смерти" }).click();
    await page.getByRole("button", { name: "Далее" }).click();
    await page.locator("#quiz-region").fill("Санкт-Петербург");
    await page.getByRole("button", { name: "Показать предварительный расчёт" }).click();

    await expect(page.locator("#quiz-result")).toBeVisible({ timeout: 20_000 });
  });
});
