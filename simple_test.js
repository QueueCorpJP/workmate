import { chromium } from 'playwright';

const LOGIN_EMAIL = 'queue@queueu-tech.jp';
const LOGIN_PASSWORD = 'John.Queue2025';
const BASE_URL = 'https://workmatechat.com';

async function testWebsite() {
  let browser;
  
  try {
    console.log('🚀 Starting workmatechat.com test...');
    
    // Launch browser with minimal configuration
    browser = await chromium.launch({
      headless: true
    });
    
    const page = await browser.newPage();
    
    // Collect errors
    const consoleMessages = [];
    const networkErrors = [];
    const jsErrors = [];
    
    page.on('console', msg => {
      consoleMessages.push(`[${msg.type()}] ${msg.text()}`);
    });
    
    page.on('pageerror', error => {
      jsErrors.push(`JS Error: ${error.message}`);
    });
    
    page.on('response', response => {
      if (!response.ok() && response.status() !== 304) {
        networkErrors.push(`${response.status()} ${response.url()}`);
      }
    });
    
    // Navigate to the website
    console.log('📋 Loading homepage...');
    await page.goto(BASE_URL, { 
      waitUntil: 'domcontentloaded',
      timeout: 30000 
    });
    
    // Get basic page info
    const title = await page.title();
    const url = page.url();
    console.log(`✅ Page loaded: ${title}`);
    console.log(`✅ Current URL: ${url}`);
    
    // Take screenshot
    await page.screenshot({ path: 'workmate_homepage.png' });
    console.log('✅ Screenshot saved');
    
    // Wait for any dynamic content
    await page.waitForTimeout(3000);
    
    // Look for login elements
    console.log('📋 Searching for login elements...');
    
    const loginElements = await page.evaluate(() => {
      const elements = [];
      
      // Find email inputs
      const emailInputs = document.querySelectorAll('input[type="email"], input[name="email"], input[placeholder*="email"], input[placeholder*="メール"]');
      elements.push(`Email inputs: ${emailInputs.length}`);
      
      // Find password inputs
      const passwordInputs = document.querySelectorAll('input[type="password"], input[name="password"]');
      elements.push(`Password inputs: ${passwordInputs.length}`);
      
      // Find login buttons
      const loginButtons = document.querySelectorAll('button:contains("ログイン"), button:contains("Login"), button:contains("サインイン"), button[type="submit"]');
      elements.push(`Login buttons: ${loginButtons.length}`);
      
      // Find all buttons
      const allButtons = document.querySelectorAll('button');
      elements.push(`Total buttons: ${allButtons.length}`);
      
      // Get button texts
      const buttonTexts = Array.from(allButtons).slice(0, 10).map((btn, i) => 
        `Button ${i+1}: "${btn.textContent?.trim() || 'No text'}"`
      );
      
      return [...elements, ...buttonTexts];
    });
    
    loginElements.forEach(element => console.log(`  ${element}`));
    
    // Try to find and test login form
    const emailInput = page.locator('input[type="email"]').first();
    const passwordInput = page.locator('input[type="password"]').first();
    
    if (await emailInput.count() > 0 && await passwordInput.count() > 0) {
      console.log('📋 Testing login form...');
      
      await emailInput.fill(LOGIN_EMAIL);
      await passwordInput.fill(LOGIN_PASSWORD);
      console.log('✅ Login credentials entered');
      
      // Look for submit button
      const submitButton = page.locator('button[type="submit"]').first();
      if (await submitButton.count() > 0) {
        console.log('📋 Clicking login button...');
        await submitButton.click();
        await page.waitForTimeout(5000);
        
        // Check if login was successful
        const newUrl = page.url();
        console.log(`✅ After login URL: ${newUrl}`);
        
        await page.screenshot({ path: 'workmate_after_login.png' });
        console.log('✅ After-login screenshot saved');
      }
    } else {
      console.log('❌ Login form not found on current page');
      
      // Look for login link
      const loginLink = page.locator('a').filter({ hasText: /ログイン|Login|サインイン/ }).first();
      if (await loginLink.count() > 0) {
        console.log('📋 Found login link, clicking...');
        await loginLink.click();
        await page.waitForTimeout(3000);
        
        // Try login form again
        const emailInputAfterNav = page.locator('input[type="email"]').first();
        const passwordInputAfterNav = page.locator('input[type="password"]').first();
        
        if (await emailInputAfterNav.count() > 0) {
          await emailInputAfterNav.fill(LOGIN_EMAIL);
          await passwordInputAfterNav.fill(LOGIN_PASSWORD);
          
          const submitBtnAfterNav = page.locator('button[type="submit"]').first();
          if (await submitBtnAfterNav.count() > 0) {
            await submitBtnAfterNav.click();
            await page.waitForTimeout(5000);
            console.log('✅ Login attempted after navigation');
          }
        }
      }
    }
    
    // Test button interactions
    console.log('📋 Testing button interactions...');
    const buttons = await page.locator('button').all();
    
    for (let i = 0; i < Math.min(buttons.length, 5); i++) {
      try {
        const button = buttons[i];
        const text = await button.textContent();
        const isVisible = await button.isVisible();
        const isEnabled = await button.isEnabled();
        
        console.log(`Button ${i+1}: "${text?.trim()}" - Visible: ${isVisible}, Enabled: ${isEnabled}`);
        
        if (isVisible && isEnabled && text && !text.includes('ログアウト') && !text.includes('削除')) {
          console.log(`  Testing click on: "${text.trim()}"`);
          await button.click();
          await page.waitForTimeout(1000);
        }
      } catch (error) {
        console.log(`  Error with button ${i+1}: ${error.message}`);
      }
    }
    
    // Final screenshot
    await page.screenshot({ path: 'workmate_final.png' });
    
    // Report results
    console.log('\n📊 Test Results Summary:');
    console.log(`Console Messages: ${consoleMessages.length}`);
    console.log(`Network Errors: ${networkErrors.length}`);
    console.log(`JavaScript Errors: ${jsErrors.length}`);
    
    if (consoleMessages.length > 0) {
      console.log('\n🔍 Console Messages (first 10):');
      consoleMessages.slice(0, 10).forEach(msg => console.log(`  ${msg}`));
    }
    
    if (networkErrors.length > 0) {
      console.log('\n🚨 Network Errors:');
      networkErrors.forEach(error => console.log(`  ${error}`));
    }
    
    if (jsErrors.length > 0) {
      console.log('\n💥 JavaScript Errors:');
      jsErrors.forEach(error => console.log(`  ${error}`));
    }
    
    console.log('\n✅ Test completed successfully!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

testWebsite();