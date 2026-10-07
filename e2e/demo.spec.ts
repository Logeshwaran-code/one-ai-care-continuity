import { test, expect } from "@playwright/test";

async function login(page, name: string) {
  await page.goto("/");
  await page.getByRole("button", { name }).click();
}

test("patient sees medicines, flags and can switch to large buttons", async ({ page }) => {
  await login(page, "Ravi (patient)");
  await expect(page.getByRole("heading", { name: "Today's medicines" })).toBeVisible();
  await expect(page.getByText("Rule: BP-BASELINE-SHIFT")).toBeVisible();
  await page.getByRole("button", { name: "Large buttons" }).click();
  await expect(page.locator("body")).toHaveClass(/big/);
});

test("family dashboard shows only consented, minimised status", async ({ page }) => {
  await login(page, "Priya (family)");
  await expect(page.getByText(/Medicine taken today/)).toBeVisible();
  await expect(page.getByText(/Next appointment/)).toBeVisible();
  await expect(page.getByText("Glycomet")).toHaveCount(0);
});

test("doctor sees summary draft that requires approval", async ({ page }) => {
  await login(page, "Dr. Meera (doctor)");
  await page.getByRole("button", { name: "Create visit summary" }).click();
  await expect(page.getByText(/clinician review required/)).toBeVisible();
  await page.getByRole("button", { name: /Approve/ }).click();
  await expect(page.getByText("Status: approved")).toBeVisible();
});

test("assistant refuses to choose an antibiotic", async ({ page }) => {
  await login(page, "Ravi (patient)");
  await page.getByLabel("Ask a question").fill("Which antibiotic should I take?");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText(/can't choose, recommend, start, stop or change/)).toBeVisible();
});
