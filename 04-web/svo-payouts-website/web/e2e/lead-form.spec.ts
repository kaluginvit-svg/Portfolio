import { expect, test } from "@playwright/test";

async function completeFreshQuiz(page: import("@playwright/test").Page) {
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
}

test.describe("Форма лида и /thanks", () => {
  test("happy path: отправка → /thanks", async ({ page }) => {
    await completeFreshQuiz(page);

    await page.getByRole("button", { name: "Оставить контакты" }).click();
    await expect(page.locator("#lead-form")).toBeInViewport();

    await page.locator("#lead-name").fill("Тест E2E");
    await page.locator("#lead-phone").fill("+79001234567");
    await page.locator("#lead-email").fill("e2e-test@example.com");
    await page.locator("#lead-region").fill("Москва");
    await page.locator("#lead-consent").click();

    await page.getByRole("button", { name: "Оставить заявку" }).click();

    await expect(page).toHaveURL(/\/thanks$/, { timeout: 15_000 });
    await expect(page.getByRole("heading", { name: /Спасибо/i })).toBeVisible();
  });

  test("валидация: без согласия показывается ошибка", async ({ page }) => {
    await completeFreshQuiz(page);
    await page.locator("#quiz-result").getByRole("button", { name: "Оставить контакты" }).click();

    await page.locator("#lead-name").fill("Тест");
    await page.locator("#lead-phone").fill("+79001112233");
    await page.locator("#lead-region").fill("Москва");

    await page.getByRole("button", { name: "Оставить заявку" }).click();

    await expect(page.getByText(/согласие на обработку персональных данных/i)).toBeVisible();
    await expect(page).not.toHaveURL(/\/thanks/);
  });
});
