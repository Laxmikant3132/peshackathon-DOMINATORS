import { test, expect } from '@playwright/test';

test.describe('UPI Analyzer', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for the analyzer section to be visible
    await page.waitForSelector('text=UPI Analyzer');
  });

  test('should mark trusted handle as safe', async ({ page }) => {
    const upiInput = page.locator('input[placeholder="Enter UPI ID (e.g. user@bank)"]');
    await upiInput.fill('sagar@oksbi');
    
    const verifyButton = page.locator('button:has-text("Verify UPI Identity")');
    await verifyButton.click();
    
    // Wait for result
    await page.waitForSelector('text=Verified Safe');
    
    const safetyLabel = page.locator('text=Verified Safe');
    await expect(safetyLabel).toBeVisible();
    
    const confidence = page.locator('text=98%');
    await expect(confidence).toBeVisible();
    
    const reason = page.locator('p.italic', { hasText: 'Verified trusted UPI handle: oksbi' });
    await expect(reason).toBeVisible();
  });

  test('should mark unknown handle as suspicious', async ({ page }) => {
    const upiInput = page.locator('input[placeholder="Enter UPI ID (e.g. user@bank)"]');
    await upiInput.fill('scam@unknown');
    
    const verifyButton = page.locator('button:has-text("Verify UPI Identity")');
    await verifyButton.click();
    
    // Wait for result
    await page.waitForSelector('text=Suspicious Activity');
    
    const safetyLabel = page.locator('text=Suspicious Activity');
    await expect(safetyLabel).toBeVisible();
    
    const indicator = page.locator('text=Unverified UPI handle');
    await expect(indicator).toBeVisible();
  });

  test('should mark invalid format as suspicious', async ({ page }) => {
    const upiInput = page.locator('input[placeholder="Enter UPI ID (e.g. user@bank)"]');
    await upiInput.fill('invalid-id');
    
    const verifyButton = page.locator('button:has-text("Verify UPI Identity")');
    await verifyButton.click();
    
    // Wait for result
    await page.waitForSelector('text=Suspicious Activity');
    
    const reason = page.locator('p.italic', { hasText: 'The provided UPI ID is invalid.' });
    await expect(reason).toBeVisible();
    
    const indicator = page.locator('text=Invalid UPI format');
    await expect(indicator).toBeVisible();
  });
});
