import https from 'https';
import http from 'http';

async function testWorkmateChatWebsite() {
  const url = 'https://workmatechat.com';
  console.log(`🚀 Testing ${url}...`);
  
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const req = https.get(url, (res) => {
      let data = '';
      
      console.log(`📊 Status Code: ${res.statusCode}`);
      console.log(`📊 Headers:`, res.headers);
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        const endTime = Date.now();
        const loadTime = endTime - startTime;
        
        console.log(`⏱️  Load Time: ${loadTime}ms`);
        console.log(`📄 Content Length: ${data.length} bytes`);
        
        // Basic HTML analysis
        const hasLoginForm = data.includes('type="email"') || data.includes('type="password"');
        const hasButtons = data.match(/<button[^>]*>/gi) || [];
        const hasInputs = data.match(/<input[^>]*>/gi) || [];
        const hasLinks = data.match(/<a[^>]*href[^>]*>/gi) || [];
        
        console.log('\n📋 HTML Analysis:');
        console.log(`✅ Login form detected: ${hasLoginForm}`);
        console.log(`✅ Buttons found: ${hasButtons.length}`);
        console.log(`✅ Input fields found: ${hasInputs.length}`);
        console.log(`✅ Links found: ${hasLinks.length}`);
        
        // Check for common frameworks/libraries
        const frameworks = {
          'React': data.includes('react') || data.includes('React'),
          'Vue': data.includes('vue') || data.includes('Vue'),
          'Angular': data.includes('angular') || data.includes('Angular'),
          'jQuery': data.includes('jquery') || data.includes('jQuery'),
          'Bootstrap': data.includes('bootstrap') || data.includes('Bootstrap')
        };
        
        console.log('\n🔧 Detected Technologies:');
        Object.entries(frameworks).forEach(([name, detected]) => {
          if (detected) console.log(`✅ ${name}: Found`);
        });
        
        // Check for potential issues
        const issues = [];
        if (data.includes('error') || data.includes('Error')) {
          issues.push('Potential error messages in HTML');
        }
        if (data.includes('404') || data.includes('500')) {
          issues.push('HTTP error codes in content');
        }
        if (!data.includes('</html>')) {
          issues.push('Incomplete HTML document');
        }
        
        if (issues.length > 0) {
          console.log('\n⚠️  Potential Issues:');
          issues.forEach(issue => console.log(`❌ ${issue}`));
        } else {
          console.log('\n✅ No obvious issues detected');
        }
        
        resolve({
          statusCode: res.statusCode,
          loadTime,
          contentLength: data.length,
          hasLoginForm,
          buttonCount: hasButtons.length,
          inputCount: hasInputs.length,
          linkCount: hasLinks.length,
          issues
        });
      });
    });
    
    req.on('error', (err) => {
      console.error(`❌ Request failed: ${err.message}`);
      reject(err);
    });
    
    req.setTimeout(10000, () => {
      console.error('❌ Request timeout');
      req.destroy();
      reject(new Error('Request timeout'));
    });
  });
}

// Run the test
testWorkmateChatWebsite()
  .then(result => {
    console.log('\n🎉 Test completed successfully!');
    console.log('📊 Summary:', result);
  })
  .catch(error => {
    console.error('❌ Test failed:', error.message);
  });