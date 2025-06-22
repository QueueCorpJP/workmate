import { chromium } from 'playwright';

async function testWebsite() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log('Navigating to http://localhost:3025/');
    await page.goto('http://localhost:3025/');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Take a screenshot
    await page.screenshot({ path: 'page_screenshot.png' });
    console.log('Screenshot saved as page_screenshot.png');
    
    // Get page title
    const title = await page.title();
    console.log('Page title:', title);
    
    // Check for console errors
    const consoleMessages = [];
    page.on('console', msg => {
      consoleMessages.push(`${msg.type()}: ${msg.text()}`);
    });
    
    // Check for network errors
    const networkErrors = [];
    page.on('response', response => {
      if (!response.ok()) {
        networkErrors.push(`${response.status()} ${response.url()}`);
      }
    });
    
    // Find all buttons on the page
    const buttons = await page.locator('button').all();
    console.log(`Found ${buttons.length} buttons on the page`);
    
    // Get button texts
    for (let i = 0; i < buttons.length; i++) {
      const buttonText = await buttons[i].textContent();
      const isVisible = await buttons[i].isVisible();
      const isEnabled = await buttons[i].isEnabled();
      console.log(`Button ${i + 1}: "${buttonText}" - Visible: ${isVisible}, Enabled: ${isEnabled}`);
    }
    
    // Test clicking the first button if it exists
    if (buttons.length > 0) {
      console.log('Testing first button click...');
      await buttons[0].click();
      await page.waitForTimeout(2000); // Wait for potential response
    }
    
    // Check for any input fields
    const inputs = await page.locator('input').all();
    console.log(`Found ${inputs.length} input fields`);
    
    // Check for any links
    const links = await page.locator('a').all();
    console.log(`Found ${links.length} links`);
    
    // Wait a bit to capture any console messages or network errors
    await page.waitForTimeout(3000);
    
    console.log('\n--- Console Messages ---');
    consoleMessages.forEach(msg => console.log(msg));
    
    console.log('\n--- Network Errors ---');
    networkErrors.forEach(error => console.log(error));
    
  } catch (error) {
    console.error('Error during testing:', error);
  } finally {
    await browser.close();
  }
}

testWebsite();