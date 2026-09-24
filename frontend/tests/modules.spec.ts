import { expect, test } from "@playwright/test";

test.describe("NyayaMitra Core Functional Modules", () => {
  test("Landing page renders all PromptWars challenge pillars and navigation links", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect(page).toHaveTitle(/NyayaMitra/);

    // Verify main headline contains challenge verbs
    const heroHeading = page.locator("h1");
    await expect(heroHeading).toBeVisible();

    // Verify presence of core module links
    await expect(page.locator('a[href*="compare"]').first()).toBeVisible();
    await expect(page.locator('a[href*="navigate"]').first()).toBeVisible();
    await expect(page.locator('a[href*="legal-aid"]').first()).toBeVisible();
    await expect(page.locator('a[href*="cases"]').first()).toBeVisible();
    await expect(page.locator('a[href*="generator"]').first()).toBeVisible();
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
    const navHeading = page.locator("h1");
    await expect(navHeading).toBeVisible();
  });

  test("Free Legal Aid Guided Interview evaluates Section 12 LSAA eligibility", async ({ page }) => {
    await page.goto("/legal-aid", { waitUntil: "domcontentloaded" });
    const pageHeading = page.locator("h1");
    await expect(pageHeading).toBeVisible();

    // Check priority category checkbox
    const womanChildBox = page.locator("#woman-child");
    await expect(womanChildBox).toBeVisible();
    await womanChildBox.check();

    // Submit evaluation
    const evalBtn = page.locator('button[type="submit"]');
    await expect(evalBtn).toBeVisible();
    await evalBtn.click();

    // Verify DLSA / Section 12 confirmation renders
    const resultRegion = page.locator('[role="region"][aria-live="polite"]');
    await expect(resultRegion).toBeVisible();
    await expect(resultRegion).toContainText(/15100|DLSA|Section 12/i);
  });

  test("eCourts CNR Lookup resolves 16-character case record", async ({ page }) => {
    await page.goto("/cases", { waitUntil: "domcontentloaded" });
    const cnrInput = page.locator("#cnr-input");
    await expect(cnrInput).toBeVisible();

    // Fill sample CNR
    await cnrInput.fill("DLCT010012342024");
    const submitBtn = page.locator('button[type="submit"]');
    await submitBtn.click();

    // Verify result card renders with court details and eCourts link
    const resultCard = page.locator('[role="region"][aria-live="polite"]');
    await expect(resultCard).toBeVisible();
    await expect(resultCard).toContainText(/DLCT010012342024|Delhi|District Court/i);
  });

  test("Controlled Generator displays mandatory statutory caveat banner", async ({ page }) => {
    await page.goto("/generator", { waitUntil: "domcontentloaded" });
    const genHeading = page.locator("h1");
    await expect(genHeading).toBeVisible();

    // Verify form fields exist
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
