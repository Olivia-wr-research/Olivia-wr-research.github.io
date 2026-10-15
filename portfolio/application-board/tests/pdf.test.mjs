import {test} from 'node:test';
import assert from 'node:assert/strict';
import {pdfText} from '../dist/pdf-text.mjs';
function mock({pages=1,text='Synthetic Python research',failure}={}){let destroyed=false,config;return {load:async()=>({GlobalWorkerOptions:{},getDocument:options=>{config=options;return {promise:failure?Promise.reject(failure):Promise.resolve({numPages:pages,getPage:async()=>({getTextContent:async()=>({items:[{str:text,hasEOL:true}]}),cleanup(){}})}),destroy:async()=>{destroyed=true;}};}}),check(){assert.ok(destroyed);assert.ok(config.data instanceof Uint8Array);assert.equal(config.url,undefined);assert.equal(config.isEvalSupported,false);assert.equal(config.useWorkerFetch,false);}};}
test('PDF extracts text and always destroys reader',async()=>{const m=mock();assert.match(await pdfText(new ArrayBuffer(20),m.load),/Python/);m.check();});
test('PDF page cap cleans up',async()=>{const m=mock({pages:21});await assert.rejects(()=>pdfText(new ArrayBuffer(20),m.load),/20 页/);m.check();});
test('image-only PDF directs user to local OCR',async()=>{const m=mock({text:''});await assert.rejects(()=>pdfText(new ArrayBuffer(20),m.load),/扫描版/);m.check();});
test('PDF text cap is enforced',async()=>{const m=mock({text:'a'.repeat(100001)});await assert.rejects(()=>pdfText(new ArrayBuffer(20),m.load),/文字过多/);m.check();});
for(const [name,expected] of [['PasswordException',/密码/],['InvalidPDFException',/无法读取/]])test(name+' gives actionable error and cleanup',async()=>{const m=mock({failure:Object.assign(Error('error'),{name})});await assert.rejects(()=>pdfText(new ArrayBuffer(20),m.load),expected);m.check();});
test('PDF oversize does not load parser',async()=>{await assert.rejects(()=>pdfText(new ArrayBuffer(6*1024*1024),()=>{throw Error('should not load');}),/5 MB/);});
