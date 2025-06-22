import { chromium, firefox, webkit } from 'playwright';

const LOGIN_EMAIL = 'queue@queueu-tech.jp';
const LOGIN_PASSWORD = 'John.Queue2025';
const BASE_URL = 'https://workmatechat.com';

async function comprehensiveTest() {
  console.log('🚀 Starting comprehensive test of workmatechat.com');
  
  // Try different browsers
  const browsers = [
    { name: 'Chromium', launcher: chromium }
  ];

  for (const browserInfo of browsers) {
    console.log(`\n📱 Testing with ${browserInfo.name}...`);
    
    try {
      const browser = await browserInfo.launcher.launch({ 
        headless: true,
        args: [
          '--no-sandbox', 
          '--disable-setuid-sandbox', 
          '--disable-dev-shm-usage', 
          '--disable-gpu',
          '--disable-web-security',
          '--no-first-run',
          '--disable-background-timer-throttling',
          '--disable-backgrounding-occluded-windows',
          '--disable-renderer-backgrounding'
        ]
      });
      
      const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 },
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
      });
      
      const page = await context.newPage();
      
      // Collect console messages and network errors
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
      
      // Test 1: Initial page load
      console.log('📋 Test 1: Loading homepage...');
      await page.goto(BASE_URL, { waitUntil: 'networkidle' });
      
      // Take screenshot
      await page.screenshot({ path: `homepage_${browserInfo.name.toLowerCase()}.png` });
      
      const title = await page.title();
      console.log(`✅ Page title: ${title}`);
      
      // Test 2: Find and test login form
      console.log('📋 Test 2: Testing login form...');
      
      // Look for login form elements
      const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]');
      const passwordInput = page.locator('input[type="password"], input[name="password"]');
      const loginButton = page.locator('button[type="submit"], button:has-text("ログイン"), button:has-text("Login"), button:has-text("サインイン")');
      
      if (await emailInput.count() > 0 && await passwordInput.count() > 0) {
        console.log('✅ Login form found');
        
        // Fill login form
        await emailInput.first().fill(LOGIN_EMAIL);
        await passwordInput.first().fill(LOGIN_PASSWORD);
        
        // Take screenshot before login
        await page.screenshot({ path: `before_login_${browserInfo.name.toLowerCase()}.png` });
        
        if (await loginButton.count() > 0) {
          await loginButton.first().click();
          await page.waitForTimeout(3000);
          
          // Take screenshot after login attempt
          await page.screenshot({ path: `after_login_${browserInfo.name.toLowerCase()}.png` });
          console.log('✅ Login attempted');
        } else {
          console.log('❌ Login button not found');
        }
      } else {
        console.log('❌ Login form not found on homepage');
        
        // Look for login link
        const loginLink = page.locator('a:has-text("ログイン"), a:has-text("Login"), a:has-text("サインイン")');
        if (await loginLink.count() > 0) {
          console.log('✅ Login link found, clicking...');
          await loginLink.first().click();
          await page.waitForTimeout(2000);
          
          // Try login form again
          const emailInputAfterNav = page.locator('input[type="email"], input[name="email"]');
          const passwordInputAfterNav = page.locator('input[type="password"], input[name="password"]');
          
          if (await emailInputAfterNav.count() > 0) {
            await emailInputAfterNav.first().fill(LOGIN_EMAIL);
            await passwordInputAfterNav.first().fill(LOGIN_PASSWORD);
            
            const submitBtn = page.locator('button[type="submit"], button:has-text("ログイン"), button:has-text("Login")');
            if (await submitBtn.count() > 0) {
              await submitBtn.first().click();
              await page.waitForTimeout(3000);
              console.log('✅ Login attempted after navigation');
            }
          }
        }
      }
      
      // Test 3: Find and test all buttons
      console.log('📋 Test 3: Testing all buttons...');
      const allButtons = await page.locator('button').all();
      console.log(`Found ${allButtons.length} buttons`);
      
      for (let i = 0; i < Math.min(allButtons.length, 10); i++) {
        try {
          const button = allButtons[i];
          const buttonText = await button.textContent();
          const isVisible = await button.isVisible();
          const isEnabled = await button.isEnabled();
          
          console.log(`Button ${i + 1}: "${buttonText?.trim()}" - Visible: ${isVisible}, Enabled: ${isEnabled}`);
          
          if (isVisible && isEnabled && buttonText && !buttonText.includes('ログアウト')) {
            console.log(`  Clicking button: "${buttonText.trim()}"`);
            await button.click();
            await page.waitForTimeout(1000);
          }
        } catch (error) {
          console.log(`  Error testing button ${i + 1}: ${error.message}`);
        }
      }
      
      // Test 4: Find and test form inputs
      console.log('📋 Test 4: Testing form inputs...');
      const textInputs = await page.locator('input[type="text"], input[type="email"], textarea').all();
      console.log(`Found ${textInputs.length} text inputs`);
      
      for (let i = 0; i < Math.min(textInputs.length, 5); i++) {
        try {
          const input = textInputs[i];
          const placeholder = await input.getAttribute('placeholder');
          const isVisible = await input.isVisible();
          
          if (isVisible) {
            console.log(`Input ${i + 1}: placeholder="${placeholder}"`);
            await input.fill('test input');
            await page.waitForTimeout(500);
            await input.clear();
          }
        } catch (error) {
          console.log(`  Error testing input ${i + 1}: ${error.message}`);
        }
      }
      
      // Test 5: Navigation links
      console.log('📋 Test 5: Testing navigation links...');
      const navLinks = await page.locator('nav a, header a, .nav a').all();
      console.log(`Found ${navLinks.length} navigation links`);
      
      for (let i = 0; i < Math.min(navLinks.length, 5); i++) {
        try {
          const link = navLinks[i];
          const href = await link.getAttribute('href');
          const text = await link.textContent();
          
          if (href && !href.includes('mailto:') && !href.includes('tel:')) {
            console.log(`Nav link ${i + 1}: "${text?.trim()}" -> ${href}`);
          }
        } catch (error) {
          console.log(`  Error testing nav link ${i + 1}: ${error.message}`);
        }
      }
      
      // Final screenshot
      await page.screenshot({ path: `final_state_${browserInfo.name.toLowerCase()}.png` });
      
      // Report results
      console.log(`\n📊 ${browserInfo.name} Test Results:`);
      console.log(`Console Messages: ${consoleMessages.length}`);
      console.log(`Network Errors: ${networkErrors.length}`);
      console.log(`JavaScript Errors: ${jsErrors.length}`);
      
      if (consoleMessages.length > 0) {
        console.log('\n🔍 Console Messages:');
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
      
      await browser.close();
      console.log(`✅ ${browserInfo.name} testing completed`);
      
    } catch (error) {
      console.log(`❌ ${browserInfo.name} testing failed: ${error.message}`);
    }
  }
  
  console.log('\n🎉 Comprehensive testing completed!');
}

comprehensiveTest().catch(console.error);