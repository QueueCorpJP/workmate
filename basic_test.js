import puppeteer from 'puppeteer';

async function testBasicFunctionality() {
  console.log('🚀 Starting basic functionality test...');
  
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--no-first-run'
      ]
    });
    
    const page = await browser.newPage();
    
    // Error tracking
    const errors = [];
    const consoleMessages = [];
    
    page.on('console', msg => {
      consoleMessages.push(`[${msg.type()}] ${msg.text()}`);
      if (msg.type() === 'error') {
        console.log('❌ Console Error:', msg.text());
      }
    });
    
    page.on('pageerror', error => {
      errors.push(`JS Error: ${error.message}`);
      console.log('💥 JavaScript Error:', error.message);
    });
    
    // Test 1: Load homepage
    console.log('📋 Test 1: Loading homepage...');
    await page.goto('https://workmatechat.com', { 
      waitUntil: 'networkidle2',
      timeout: 30000 
    });
    
    const title = await page.title();
    console.log(`✅ Page title: ${title}`);
    
    // Test 2: Wait for React to load
    console.log('📋 Test 2: Waiting for React app to load...');
    await page.waitForTimeout(3000);
    
    // Test 3: Check for interactive elements
    console.log('📋 Test 3: Checking for interactive elements...');
    
    const buttons = await page.$$('button');
    const links = await page.$$('a');
    const inputs = await page.$$('input');
    
    console.log(`✅ Found ${buttons.length} buttons`);
    console.log(`✅ Found ${links.length} links`);  
    console.log(`✅ Found ${inputs.length} inputs`);
    
    // Test 4: Try clicking available buttons
    if (buttons.length > 0) {
      console.log('📋 Test 4: Testing button interactions...');
      for (let i = 0; i < Math.min(buttons.length, 5); i++) {
        try {
          const button = buttons[i];
          const text = await button.evaluate(el => el.textContent?.trim());
          const isVisible = await button.isIntersectingViewport();
          
          if (isVisible && text) {
            console.log(`  Testing button: "${text}"`);
            await button.click();
            await page.waitForTimeout(1000);
          }
        } catch (error) {
          console.log(`  Button ${i} click failed: ${error.message}`);
        }
      }
    }
    
    // Test 5: Check page navigation
    console.log('📋 Test 5: Testing navigation...');
    const navigationLinks = await page.$$('nav a, header a, .nav a');
    
    if (navigationLinks.length > 0) {
      console.log(`✅ Found ${navigationLinks.length} navigation links`);
      
      for (let i = 0; i < Math.min(navigationLinks.length, 3); i++) {
        try {
          const link = navigationLinks[i];
          const href = await link.evaluate(el => el.getAttribute('href'));
          const text = await link.evaluate(el => el.textContent?.trim());
          
          if (href && !href.startsWith('mailto:') && !href.startsWith('tel:')) {
            console.log(`  Testing link: "${text}" -> ${href}`);
            // Don't actually navigate, just check if clickable
            const isClickable = await link.evaluate(el => {
              const style = window.getComputedStyle(el);
              return style.pointerEvents !== 'none' && style.display !== 'none';
            });
            console.log(`    Clickable: ${isClickable}`);
          }
        } catch (error) {
          console.log(`  Link ${i} test failed: ${error.message}`);
        }
      }
    }
    
    // Test 6: Performance metrics
    console.log('📋 Test 6: Performance metrics...');
    const metrics = await page.metrics();
    console.log(`✅ Timestamp: ${metrics.Timestamp}`);
    console.log(`✅ DOM Nodes: ${metrics.Nodes}`);
    console.log(`✅ JS Heap Used: ${Math.round(metrics.JSHeapUsedSize / 1024 / 1024)}MB`);
    
    // Final screenshot
    await page.screenshot({ path: 'workmate_test_final.png' });
    
    // Summary
    console.log('\n📊 Test Summary:');
    console.log(`✅ Page loaded successfully: ${title}`);
    console.log(`✅ Interactive elements: ${buttons.length + links.length + inputs.length}`);
    console.log(`✅ JavaScript errors: ${errors.length}`);
    console.log(`✅ Console messages: ${consoleMessages.length}`);
    
    if (errors.length > 0) {
      console.log('\n💥 JavaScript Errors:');
      errors.forEach(error => console.log(`  ${error}`));
    }
    
    if (consoleMessages.filter(msg => msg.includes('[error]')).length > 0) {
      console.log('\n❌ Console Errors:');
      consoleMessages.filter(msg => msg.includes('[error]')).forEach(msg => console.log(`  ${msg}`));
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
  
  console.log('\n🎉 Basic functionality test completed!');
}

testBasicFunctionality();