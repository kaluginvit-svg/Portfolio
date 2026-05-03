import { expect, test } from "@playwright/test";

test.describe("Fresh flow", () => {
  test("hero → полный расчёт → блок результата", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("button", { name: "Узнать, какие выплаты положены" }).first().click();

    await page.getByRole("button", { name: "Был мобилизован" }).click();
    await page.getByRole("button", { name: "Супруг или супруга" }).click();
    await page.getByRole("button", { name: "Только я" }).click();

    await page.getByRole("checkbox", { name: "Свидетельство о смерти" }).click();
    await page.getByRole("button", { name: "Далее" }).click();

    await page.locator("#quiz-region").fill("Москва");
    await page.getByRole("button", { name: "Показать предварительный расчёт" }).click();

    await expect(page.locator("#quiz-result")).toBeVisible({ timeout: 20_000 });
    await expect(page.locator("#quiz-result")).toHaveAttribute(
      "aria-label",
      "Предварительный расчёт выплат",
    );
  });
});
