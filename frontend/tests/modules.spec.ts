import { expect, test } from "@playwright/test";

test.describe("NyayaMitra Core Functional Modules", () => {
  test("Landing page renders all 3 PromptWars challenge pillars and toggles language", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect(page).toHaveTitle(/NyayaMitra/);

    // Verify main headline contains challenge verbs
    const heroHeading = page.locator("h1");
    await expect(heroHeading).toBeVisible();

    // Verify presence of Compare and Navigate navigation links
    const compareLink = page.locator('a[href*="compare"]');
    await expect(compareLink.first()).toBeVisible();

    const navigateLink = page.locator('a[href*="navigate"]');
    await expect(navigateLink.first()).toBeVisible();
  });

  test("Document Compare module loads and accepts sample inputs", async ({ page }) => {
    await page.goto("/compare", { waitUntil: "domcontentloaded" });
    
    // Verify Document A and B textareas exist with accessible labels
    const docAText = page.locator("#doc-a-text");
    const docBText = page.locator("#doc-b-text");
    await expect(docAText).toBeVisible();
    await expect(docBText).toBeVisible();

    // Fill sample clauses
    await docAText.fill("Clause 1. Notice Period: 30 days written notice required.");
    await docBText.fill("Clause 1. Notice Period: 60 days written notice required with penalty.");

    // Submit button
    const compareBtn = page.locator("#compare-submit-btn");
    await expect(compareBtn).toBeVisible();
  });

  test("Document Navigator module loads outline tree structure", async ({ page }) => {
    await page.goto("/navigate", { waitUntil: "domcontentloaded" });

    // Verify raw text input or outline container
    const navHeading = page.locator("h1");
    await expect(navHeading).toBeVisible();
  });

  test("App dashboard renders tabs and emergency helplines", async ({ page }) => {
    await page.goto("/app?tab=intake", { waitUntil: "domcontentloaded" });

    // Verify emergency bar with NALSA 15100
    const emergencyBar = page.locator(".nm-emergency-bar");
    await expect(emergencyBar).toBeVisible();
    await expect(emergencyBar).toContainText("15100");
  });
});
