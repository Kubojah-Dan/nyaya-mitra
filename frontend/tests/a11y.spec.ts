import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const routes = ["/", "/app", "/compare", "/navigate", "/legal-aid", "/cases", "/generator"];

for (const route of routes) {
  test(`has no automatically detectable accessibility violations on ${route}`, async ({ page }) => {
    await page.goto(route, { waitUntil: "domcontentloaded" });
    await page.waitForSelector("#main-content");

    const accessibilityScanResults = await new AxeBuilder({ page })
      .disableRules(["color-contrast"])
      .exclude("nextjs-portal")
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });
}
