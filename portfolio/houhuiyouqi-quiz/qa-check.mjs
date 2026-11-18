/* Browser QA for draft prelaunch version of the friendship quiz.
 * Automated tests measure behavior; they do not validate subjective writing quality.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.QUIZ_PLAYWRIGHT);
const browser=await chromium.launch({headless:true,executablePath:process.env.QUIZ_CHROME,args:['--no-sandbox']});
const root='http://127.0.0.1:8765/apps/houhuiyouqi-quiz/';
const output=process.env.QUIZ_QA_OUT||'/tmp/hhyq-qa';
fs.mkdirSync(output,{recursive:true});
const events=[];
const context=await browser.newContext({viewport:{width:390,height:844},acceptDownloads:true,deviceScaleFactor:1});
const page=await context.newPage();
page.on('pageerror',err=>events.push(err.message));
page.setDefaultTimeout(15000);

function status(label){console.log('[PASS]',label)}
async function viewportNoOverflow(label){
  const v=await page.evaluate(()=>({document:document.documentElement.scrollWidth,window:window.innerWidth}));
  assert.ok(v.document<=v.window+2,label+' overflow '+JSON.stringify(v));
}
async function shot(label){await page.screenshot({path:path.join(output,label+'.png'),fullPage:true,animations:'disabled'})}
async function captureForSizes(label) {
 for(const w of [320,375,390,768,1280]){
  await page.setViewportSize({width:w,height:w<500?844:900});
  await viewportNoOverflow(label+' '+w);
 }
 await page.setViewportSize({width:390,height:844});
}
async function pngDownload(label){
 const [download]=await Promise.all([page.waitForEvent('download',{timeout:25000}),page.locator('#download').click()]);
 const file=await download.path();assert.ok(file,'download path');
 const buf=fs.readFileSync(file);assert.ok(buf.length>3500,'PNG too small: '+buf.length);
 assert.equal(buf.toString('hex',0,8),'89504e470d0a1a0a','PNG header');
 assert.equal(buf.readUInt32BE(16),1080,'PNG width');assert.equal(buf.readUInt32BE(20),1920,'PNG height');
 status('download '+label+' 1080x1920 PNG');
}
await page.goto(root,{waitUntil:'domcontentloaded'});
await page.locator('#start').waitFor();
await captureForSizes('home');
await shot('01-home-mobile');
status('home across viewport sizes');
await page.locator('#start').click();
assert.equal(await page.locator('[data-ans]').count(),4);
assert.equal(await page.locator('#forward').isDisabled(),true);
await page.locator('[data-ans="1"]').click();
assert.equal(await page.locator('[data-ans="1"]').getAttribute('aria-pressed'),'true');
assert.equal(await page.locator('#forward').isEnabled(),true);
await page.locator('#forward').click();
await page.locator('#back').click();
assert.equal(await page.locator('[data-ans="1"]').getAttribute('aria-pressed'),'true');
await page.locator('#forward').click();
status('selection persistence, back-navigation, progress');
await shot('02-question-mobile');
for(let i=1;i<10;i++){
  const choice=i%4;
  await page.locator('[data-ans="'+choice+'"]').click();
  await page.locator('#forward').click();
}
await page.locator('.v2-result-grid').waitFor();
assert.equal(await page.locator('[data-template]').count(),4);
assert.equal(await page.locator('.v2-evidence-row').count(),3,'Personalized answer evidence missing');
await captureForSizes('result');
await shot('03-result-mobile');
await page.setViewportSize({width:1280,height:900});
await shot('04-result-desktop');
await page.setViewportSize({width:390,height:844});
status('complete ten questions, personalized result, 4 template choices');
const before=await page.locator('#character-preview').inputValue();
const b64=await page.evaluate(()=>{
 const c=document.createElement('canvas');c.width=80;c.height=120;
 const ctx=c.getContext('2d');ctx.fillStyle='#d5896c';ctx.fillRect(0,0,80,120);
 ctx.fillStyle='#fff';ctx.fillRect(10,10,60,30);
 return c.toDataURL('image/png').split(',')[1];
});
await page.locator('#photo-upload').setInputFiles({name:'synthetic-qa-picture.png',mimeType:'image/png',buffer:Buffer.from(b64,'base64')});
await page.locator('[data-character-photo]').waitFor();
assert.equal(await page.locator('[data-character-photo]').count(),1);
await page.locator('#photo-focus').evaluate(el=>{el.value='33';el.dispatchEvent(new Event('input',{bubbles:true}))});
assert.equal(await page.locator('#photo-focus-value').innerText(),'33%');
await page.reload({waitUntil:'domcontentloaded'});
await page.locator('#photo-focus').waitFor();
assert.equal(await page.locator('#photo-focus').inputValue(),'33');
assert.equal(await page.locator('#character-preview').inputValue(),before);
await page.locator('[data-character-photo]').waitFor();
assert.ok((await page.locator('[data-character-photo]').getAttribute('src')).startsWith('data:image/jpeg'), 'photo in IndexedDB not recovered');
status('photo upload, local persistence and portrait focus survive reload');
await shot('05-photo-uploaded');
for(const template of ['cinema','ticket','magazine','danmu']){
 await page.locator('[data-template="'+template+'"]').click();
 assert.ok((await page.locator('[data-template="'+template+'"]').getAttribute('class')).includes('active'));
 await pngDownload(template);
}
await shot('06-template-chooser');
const ids=['li','xu','zhang','ma','wen','wang','qing','bai'];
for(const id of ids){
 await page.goto(root+'?r='+id,{waitUntil:'domcontentloaded'});
 await page.locator('.v2-result-grid').waitFor();
 assert.equal(await page.locator('#poster-chooser').isVisible(),true);
 assert.ok((await page.locator('.v2-result-head h1').innerText()).length>3);
 assert.ok((await page.locator('.v2-banner').innerText()).includes('公共静态资源'));await page.waitForFunction(()=>{const i=document.querySelector('[data-character-photo]');return i?.complete && i.naturalWidth>0});assert.ok((await page.locator('[data-character-photo]').getAttribute('src')).includes('./photos/'));
 if(id==='xu') await shot('07-share-result');
}
status('8/8 deep-link result screens and truthful photo notice');
await context.close();
const clean=await browser.newContext({viewport:{width:375,height:812}});
const fresh=await clean.newPage();
await fresh.goto(root+'?r=wen',{waitUntil:'domcontentloaded'});
await fresh.locator('#poster-chooser').waitFor();
await fresh.waitForFunction(()=>{const i=document.querySelector('[data-character-photo]');return i?.complete && i.naturalWidth>0});assert.ok((await fresh.locator('[data-character-photo]').getAttribute('src')).includes('./photos/'),'fresh visitor must see published photo');
assert.equal(await fresh.locator('.v2-evidence-row').count(),0,'personalized answers incorrectly leaked to share recipients');
await fresh.screenshot({path:path.join(output,'08-fresh-browser-result.png'),fullPage:true,animations:'disabled'});
status('fresh visitor sees public cast photo but no local custom upload or private answer trail');
await clean.close();
assert.deepEqual(events,[],'Browser page errors');
status('no JavaScript page errors');
await browser.close();
console.log('[RESULT] Browser QA PASS. Screenshots in '+output);
