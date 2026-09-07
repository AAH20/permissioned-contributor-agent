// Optional local tooling: npm install; CHROME_PATH=/path/to/chrome node scripts/screenshot.cjs
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');
const puppeteer = require(process.env.PUPPETEER_MODULE || 'puppeteer-core');
(async()=>{
  if(!process.env.CHROME_PATH)throw Error('Set CHROME_PATH to an installed Chrome executable');
  const root=path.resolve(__dirname,'..');
  const browser=await puppeteer.launch({executablePath:process.env.CHROME_PATH,headless:true});
  try {
    const page=await browser.newPage();
    await page.setViewport({width:1440,height:1100,deviceScaleFactor:1});
    const errors=[];page.on('pageerror',e=>errors.push(String(e)));
    await page.goto(pathToFileURL(path.join(root,'evidence/report.html')).href,{waitUntil:'load'});
    const expected=JSON.parse(fs.readFileSync(path.join(root,'evidence/evaluation.json'),'utf8')).tests_run;
    const text=await page.$eval('body',el=>el.innerText);
    if(!text.includes(expected+' passed')||!text.includes('BLOCKED'))throw Error('Stale or misleading report');
    if(errors.length)throw Error(errors.join('\n'));
    await page.screenshot({path:path.join(root,'evidence/demo.png'),fullPage:true});
    console.log('Captured public synthetic report.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
