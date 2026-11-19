/* V6 release browser checks. Browser emulation does not replace testing on real phones. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const isWebkit=process.env.HHYQ_ENGINE==='webkit';
const {chromium,webkit}=require(process.env.HHYQ_PW);
const browser=isWebkit
 ? await webkit.launch({headless:true})
 : await chromium.launch({headless:true,executablePath:process.env.HHYQ_CHROME||'/usr/bin/google-chrome',args:['--no-sandbox']});
const root='http://127.0.0.1:'+(isWebkit?'8767':'8765')+'/apps/houhuiyouqi-quiz/';
const out=process.env.HHYQ_OUT||(isWebkit?'/tmp/hhyq-mobile-results':'/tmp/hhyq-qa');
const ids=['li','xu','zhang','ma','wen','wang','qing','bai'];
fs.mkdirSync(out,{recursive:true});
const iphone='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1';
const context=await browser.newContext({viewport:{width:390,height:844},acceptDownloads:true,...(isWebkit?{userAgent:iphone,isMobile:true,hasTouch:true,deviceScaleFactor:2}:{})});
const page=await context.newPage();
page.setDefaultTimeout(20000);
const errors=[];
page.on('pageerror',e=>errors.push(e.message));
async function checkLoaded(selector,count=1){
  await page.waitForFunction(({selector,count})=>{
    const ims=[...document.querySelectorAll(selector)];
    return ims.length===count&&ims.every(im=>im.complete&&im.naturalWidth>0&&im.getBoundingClientRect().width>30);
  },{selector,count},{timeout:25000});
}
async function checkWidth(label){
 const v=await page.evaluate(()=>({doc:document.documentElement.scrollWidth,inner:window.innerWidth}));
 assert.ok(v.doc<=v.inner+2,label+' overflow '+JSON.stringify(v));
}
await page.goto(root,{waitUntil:'domcontentloaded'});
await page.locator('#start').waitFor();
assert.equal(await page.locator('.cast img[data-hhyq-photo]').count(),8);
await checkLoaded('.cast figure:nth-child(-n+4) img',4);
await page.locator('.cast').evaluate(el => { el.scrollLeft = el.scrollWidth; el.dispatchEvent(new Event('scroll')); });
await checkLoaded('.cast img[data-hhyq-photo]',8);
await page.locator('.cast').evaluate(el => { el.scrollLeft = 0; });
await checkWidth('home');
const strip=await page.locator('.cast').evaluate(el=>({width:el.clientWidth,scroll:el.scrollWidth}));
assert.ok(strip.width>275&&strip.scroll>strip.width,'mobile photo carousel hidden or not scrollable');
await page.screenshot({path:path.join(out,'01-home.png'),fullPage:true,animations:'disabled'});
if(!isWebkit){
 for(const w of [320,375,390,768,1280]){await page.setViewportSize({width:w,height:844});await checkWidth('home '+w);}
 await page.setViewportSize({width:390,height:844});
}
const largeAtHome=await page.evaluate(()=>performance.getEntriesByType('resource').filter(x=>x.name.includes('/v6/photos-hd/')).length);
assert.equal(largeAtHome,0,'Heavy original photos loaded on home screen');
console.log('PASS home loads small portraits only; eight images swipe correctly');
const photoBase='docs/apps/houhuiyouqi-quiz/v6/';
const homeBytes=ids.reduce((n,id)=>n+fs.statSync(photoBase+'photos-thumb/'+id+'.webp').size,0);
const screenBytes=ids.reduce((n,id)=>n+fs.statSync(photoBase+'photos-screen/'+id+'.webp').size,0);
assert.ok(homeBytes<600000,'Home portrait payload too large: '+homeBytes);
assert.ok(screenBytes<2400000,'Screen photos payload too large: '+screenBytes);
console.log('PASS WebP byte budgets: 8 thumbnails '+homeBytes+' bytes, 8 screen photos '+screenBytes+' bytes');

/* No old choices or poster preferences may survive a fresh visit. */
await page.evaluate(()=>{
  sessionStorage.setItem('hhyq-progress',JSON.stringify({step:6,answers:Array(10).fill(2)}));
  localStorage.setItem('hhyq-template','magazine');
});
await page.reload({waitUntil:'domcontentloaded'});
await page.locator('#start').waitFor();
assert.equal(await page.locator('#continue').count(),0,'Legacy resume button must be removed');
assert.equal(await page.evaluate(()=>sessionStorage.getItem('hhyq-progress')),null,'Legacy answer storage not removed');
assert.equal(await page.evaluate(()=>localStorage.getItem('hhyq-template')),null,'Legacy poster choice not removed');
await page.locator('#start').click();
assert.equal(await page.locator('[role="progressbar"]').getAttribute('aria-valuenow'),'1','New quiz should start on question 1');
await page.locator('[data-ans="1"]').click();
await page.waitForFunction(()=>Number(document.querySelector('[role="progressbar"]')?.getAttribute('aria-valuenow'))===2);
assert.equal(await page.evaluate(()=>sessionStorage.getItem('hhyq-progress')),null,'New quiz progress must not be saved');
await page.locator('#back').click();
assert.equal(await page.locator('[data-ans="1"]').getAttribute('aria-pressed'),'true','Back must preserve current-run answers');
await page.locator('[data-ans="0"]').click();
await page.waitForFunction(()=>Number(document.querySelector('[role="progressbar"]')?.getAttribute('aria-valuenow'))===2);
await page.reload({waitUntil:'domcontentloaded'});
await page.locator('#start').waitFor();
assert.equal(await page.locator('#continue').count(),0,'Reloading mid-quiz offered resume');
assert.equal(await page.locator('[data-ans]').count(),0,'Reload leaked last run choices');
console.log('PASS fresh start, old selections removed, back/edit preserved during current run');

for(const id of ids){
 await page.goto(root+'?r='+id,{waitUntil:'domcontentloaded'});
 await page.locator('#portrait-img').waitFor();
 await checkLoaded('#portrait-img');
 assert.ok((await page.locator('#portrait-img').getAttribute('src')).includes('/v6/photos-screen/'+id+'.webp'),'portrait mismatched '+id);
 const firstResultHeavy=await page.evaluate(()=>performance.getEntriesByType('resource').filter(x=>x.name.includes('/v6/photos-hd/')).length);
 assert.equal(firstResultHeavy,0,'HD poster image loaded before the user reaches poster editor');
 assert.ok(await page.locator('#poster-chooser').isVisible(),'poster missing '+id);
 assert.equal(await page.locator('.ev').count(),0,'Private answers exposed in share result '+id);
 await checkWidth('result '+id);
 await page.goto(root+'v6/share/'+id+'.html',{waitUntil:'domcontentloaded'});
 await checkLoaded('.pic img');
 const og=await page.locator('meta[property="og:image"]').getAttribute('content');
 assert.ok(og.endsWith('/v6/share-cover-'+id+'.jpg'),'Incorrect social share image '+id);
 await checkWidth('share '+id);
}
await page.screenshot({path:path.join(out,'02-share.png'),fullPage:true,animations:'disabled'});
console.log('PASS 8/8 direct result pages, photos, and phone share landings');
await page.goto(root,{waitUntil:'domcontentloaded'});
await page.locator('#start').click();
for(let i=0;i<10;i++){
 assert.equal(await page.locator('[data-ans]').count(),4,'options on question '+(i+1));
 await page.locator('[data-ans="'+(i%4)+'"]').click();
 if(i<9)await page.waitForFunction(expected=>
   Number(document.querySelector('[role="progressbar"]')?.getAttribute('aria-valuenow'))===expected
 ,i+2,{timeout:12000});
}
await page.locator('.verdict').waitFor();
await checkLoaded('#portrait-img');
assert.equal(await page.locator('.ev').count(),3,'Personalized result explanation missing');
assert.equal(await page.locator('[data-template]').count(),4,'Expected 4 poster choices');
assert.equal(new URL(page.url()).searchParams.has('r'),false,'Completed quiz should not persist result in URL');
await page.screenshot({path:path.join(out,'03-result.png'),fullPage:true,animations:'disabled'});
console.log('PASS full 10-question automatic advance, three answer clues, four templates');
if(isWebkit){
 await page.locator('#download').click();
 await page.locator('#poster-sheet').waitFor({timeout:35000});
 await page.waitForFunction(()=>{const im=document.querySelector('#sheet-img');return im?.complete&&im.naturalWidth===1080&&im.naturalHeight===1920},{},{timeout:30000});
 await page.screenshot({path:path.join(out,'04-ios-save.png'),fullPage:false,animations:'disabled'});
 await page.locator('#sheet-close').click();
 assert.equal(await page.locator('#poster-sheet').count(),0);
 await page.reload({waitUntil:'domcontentloaded'});
 await page.locator('#start').waitFor();
 assert.equal(await page.locator('.verdict').count(),0,'Safari reload retained old result');
 await context.close();
 const wechat='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.51';
 const wx=await browser.newContext({userAgent:wechat,viewport:{width:375,height:812},isMobile:true,hasTouch:true,deviceScaleFactor:2});
 const wp=await wx.newPage();
 wp.on('pageerror',e=>errors.push(e.message));
 await wp.goto(root+'?r=wen',{waitUntil:'domcontentloaded'});
 await wp.waitForFunction(()=>{const im=document.querySelector('#portrait-img');return im?.complete&&im.naturalWidth>0});
 await wp.locator('#download').click();
 await wp.locator('#poster-sheet').waitFor({timeout:35000});
 assert.ok((await wp.locator('#poster-sheet').innerText()).includes('长按'),'WeChat save instruction absent');
 await wp.waitForFunction(()=>{const im=document.querySelector('#sheet-img');return im?.complete&&im.naturalWidth===1080});
 await wp.screenshot({path:path.join(out,'05-wechat-save.png'),fullPage:false,animations:'disabled'});
 await wx.close();
 console.log('PASS Safari/WebKit and WeChat user-agent poster save sheets');
}else{
 await page.locator('[data-template="magazine"]').click();
 assert.equal(await page.locator('[data-template="magazine"]').getAttribute('aria-pressed'),'true');
 const [download]=await Promise.all([page.waitForEvent('download',{timeout:35000}),page.locator('#download').click()]);
 const buf=fs.readFileSync(await download.path());
 assert.ok(buf.length>5000,'Export too small');
 assert.equal(buf.toString('hex',0,8),'89504e470d0a1a0a','Not PNG');
 assert.equal(buf.readUInt32BE(16),1080,'Wrong PNG width');
 assert.equal(buf.readUInt32BE(20),1920,'Wrong PNG height');
 console.log('PASS Chromium poster export PNG 1080x1920');
 await page.reload({waitUntil:'domcontentloaded'});
 await page.locator('#start').waitFor();
 assert.equal(await page.locator('.verdict').count(),0,'Chrome reload retained old result');
 await context.close();
}
const fallbackContext=await browser.newContext({viewport:{width:375,height:812},...(isWebkit?{userAgent:iphone,isMobile:true,hasTouch:true}:{})});
await fallbackContext.route('**/v6/photos-hd/li.webp',route=>route.abort());
const fallback=await fallbackContext.newPage();
fallback.on('pageerror',e=>errors.push(e.message));
await fallback.goto(root+'?r=li',{waitUntil:'domcontentloaded'});
await fallback.waitForFunction(()=>{
  const im=document.querySelector('#portrait-img');
  return im?.complete&&im.naturalWidth>0&&im.currentSrc.includes('share-cover-li.jpg');
},{},{timeout:25000});
await fallbackContext.close();
console.log('PASS WebP network failure -> visible JPG fallback');
assert.deepEqual(errors,[],'Unexpected browser JavaScript errors');
await browser.close();
console.log('SUCCESS: HOUHUIYOUQI V6 '+(isWebkit?'WEBKIT':'CHROMIUM')+' ACCEPTANCE');
