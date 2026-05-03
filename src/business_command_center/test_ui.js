const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  
  page.on('pageerror', error => {
    console.log('PAGE ERROR:', error.message);
  });
  
  console.log("Navigating to localhost:3000...");
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle2' });
  
  console.log("Clicking button...");
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const btn = buttons.find(b => b.textContent.includes('Buscar o ejecutar comando...'));
    if (btn) btn.click();
  });
  
  // wait 1 second
  await new Promise(r => setTimeout(r, 1000));
  
  const hasError = await page.evaluate(() => !!document.getElementById('__next_error__'));
  if (hasError) {
    const errText = await page.evaluate(() => document.body.innerText);
    console.error("CRASH AFTER CLICK:", errText);
  }
  
  await browser.close();
})();
