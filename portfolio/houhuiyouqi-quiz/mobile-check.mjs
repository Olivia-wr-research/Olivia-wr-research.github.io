/* iOS Safari-engine and WeChat UA prelaunch smoke tests.
   WebKit on Linux is an engine test, NOT an iPhone hardware or WeChat app certification. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {webkit}=require(process.env.MOBILE_PW);
const browser=await webkit.launch({headless:true});
const root='http://127.0.0.1:8767/apps/houhuiyouqi-quiz/';
const output=process.env.MOBILE_QA_OUT||'/tmp/hhyq-mobile';
fs.mkdirSync(output,{recursive:true});
const safariUA='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1';
const wechatUA='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.51';
const events=[];
const context=await browser.newContext({userAgent:safariUA,viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:2});
const page=await context.newPage();
page.on('pageerror',e=>events.push(e.message));
page.setDefaultTimeout(20000);
const ids=['li','xu','zhang','ma','wen','wang','qing','bai'];
for(const id of ids){
 await page.goto(root+'?r='+id,{waitUntil:'domcontentloaded'});
 await page.locator('.v2-result-grid').waitFor();
 await page.waitForFunction(()=>{const im=document.querySelector('[data-character-photo]');return im?.complete&&im.naturalWidth>=450;});
 const photo=await page.locator('[data-character-photo]').getAttribute('src');
 assert.equal(photo,'./photos/'+id+'.webp','wrong static photo for '+id);
 const v=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,inner:window.innerWidth}));
 assert.ok(v.scroll<=v.inner+2,'horizontal overflow on WebKit '+id+' '+JSON.stringify(v));
}
console.log('[PASS] 8/8 portraits loaded in iPhone Safari-engine with no layout overflow');
await page.goto(root,{waitUntil:'domcontentloaded'});
await page.locator('#start').click();
for(let i=0;i<10;i++){
 await page.locator('[data-ans="'+(i%4)+'"]').click();
 await page.locator('#forward').click();
}
await page.locator('.v2-result-grid').waitFor();
assert.equal(await page.locator('.v2-evidence-row').count(),3);
await page.locator('#fast-poster').click();
await page.locator('[data-template="cinema"]').waitFor();
await page.screenshot({path:path.join(output,'01-ios-result.png'),fullPage:true,animations:'disabled'});
await page.locator('#download').click();
const modal=page.locator('#poster-save-sheet');
await modal.waitFor();
const img=page.locator('#poster-save-image');
await page.waitForFunction(()=>{const im=document.querySelector('#poster-save-image');return im?.complete&&im.naturalWidth===1080&&im.naturalHeight===1920;});
assert.ok((await img.getAttribute('src')).startsWith('data:image/png;base64,'));
assert.ok((await modal.innerText()).includes('长按'));
await page.screenshot({path:path.join(output,'02-ios-save-sheet.png'),fullPage:false,animations:'disabled'});
await page.locator('#poster-save-close').click();
assert.equal(await modal.count(),0);
console.log('[PASS] iOS Safari-engine: 10 questions, 3 answer clues, 1080x1920 share-sheet, close');
await context.close();
const wx=await browser.newContext({userAgent:wechatUA,viewport:{width:375,height:812},isMobile:true,hasTouch:true,deviceScaleFactor:2});
const wxPage=await wx.newPage();
wxPage.on('pageerror',e=>events.push(e.message));
await wxPage.goto(root+'?r=wen',{waitUntil:'domcontentloaded'});
await wxPage.waitForFunction(()=>{const im=document.querySelector('[data-character-photo]');return im?.complete&&im.naturalWidth>0;});
await wxPage.locator('#download').click();
await wxPage.locator('#poster-save-sheet').waitFor();
await wxPage.waitForFunction(()=>{const im=document.querySelector('#poster-save-image');return im?.complete&&im.naturalWidth===1080;});
await wxPage.screenshot({path:path.join(output,'03-wechat-ua-save-sheet.png'),fullPage:false,animations:'disabled'});
console.log('[PASS] WeChat user agent under WebKit: public portrait + long-press save overlay');
await wx.close();
assert.deepEqual(events,[],'WebKit runtime exceptions: '+JSON.stringify(events));
await browser.close();
console.log('[RESULT] Mobile emulation PASS; physical iPhone & WeChat app remain untested.');
