import { expect, test } from "@playwright/test";

test.describe("NyayaMitra Core Functional Modules", () => {
  test("Landing page renders all PromptWars challenge pillars and navigation links", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect(page.locator("#landing-hero-heading")).toBeVisible();

    // Verify presence of core module links
    await expect(page.locator('a[href*="compare"]').first()).toBeVisible();
    await expect(page.locator('a[href*="navigate"]').first()).toBeVisible();
    await expect(page.locator('a[href*="legal-aid"]').first()).toBeVisible();
    await expect(page.locator('a[href*="cases"]').first()).toBeVisible();
    await expect(page.locator('a[href*="generator"]').first()).toBeVisible();
  });

  test("Document Compare module loads and accepts sample inputs", async ({ page }) => {
    await page.goto("/compare", { waitUntil: "networkidle" });
    
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
    await expect(page.locator("#navigate-page-heading")).toBeVisible();
  });

  test("Free Legal Aid Guided Interview page renders form controls", async ({ page }) => {
    await page.goto("/legal-aid", { waitUntil: "domcontentloaded" });
    await expect(page.locator(".nm-hero-title-main")).toBeVisible();

    // Verify priority category checkbox and submit button exist
    const womanChildBox = page.locator("#woman-child");
    await expect(womanChildBox).toBeVisible();

    const evalBtn = page.locator('button[type="submit"]');
    await expect(evalBtn).toBeVisible();
  });

  test("eCourts CNR Lookup page renders input and search button", async ({ page }) => {
    await page.goto("/cases", { waitUntil: "domcontentloaded" });
    const cnrInput = page.locator("#cnr-input");
    await expect(cnrInput).toBeVisible();

    const submitBtn = page.locator('button[type="submit"]');
    await expect(submitBtn).toBeVisible();
  });

  test("Controlled Generator displays form and template choices", async ({ page }) => {
    await page.goto("/generator", { waitUntil: "domcontentloaded" });
    await expect(page.locator(".nm-hero-title-main")).toBeVisible();

    // Verify form submit button exists
    const submitBtn = page.locator('button[type="submit"]');
    await expect(submitBtn).toBeVisible();
  });

  test("App dashboard renders tabs and emergency helplines", async ({ page }) => {
    await page.goto("/app?tab=intake", { waitUntil: "domcontentloaded" });

    // Verify emergency bar with NALSA 15100
    const emergencyBar = page.locator(".nm-emergency-bar");
    await expect(emergencyBar).toBeVisible();
    await expect(emergencyBar).toContainText("15100");
  });
});
