// Text extraction only. PDF bytes stay in this browser; no URL or remote service.
export async function pdfText(buffer, load = () => import('./pdf.min.mjs')) {
 if (!(buffer instanceof ArrayBuffer) || buffer.byteLength > 5 * 1024 * 1024) throw Error('PDF 最大 5 MB');
 const pdfjs = await load();
 pdfjs.GlobalWorkerOptions.workerSrc = new URL('./pdf.worker.min.mjs', import.meta.url).href;
 const task = pdfjs.getDocument({data:new Uint8Array(buffer),isEvalSupported:false,useWorkerFetch:false,useWasm:false,disableFontFace:true,enableXfa:false,verbosity:0});
 let timer;
 try {
  const extract = async () => {
   const doc = await task.promise;
   if (doc.numPages > 20) throw Error('简历最多 20 页，请选取相关页面');
   let text = '';
   for(let n=1;n<=doc.numPages;n++) {
    const page = await doc.getPage(n);
    const content = await page.getTextContent();
    for(const item of content.items) if(typeof item.str==='string') {
     text += item.str + (item.hasEOL?'\n':' ');
     if(text.length>100000) throw Error('文字过多，请只保留教育、项目与技能部分');
    }
    text+='\n';page.cleanup();
   }
   if(text.trim().length<10) throw Error('没有读到足够文字；扫描版 PDF 请先在本机识别文字，再粘贴');
   return text;
  };
  return await Promise.race([extract(),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('PDF 读取超时，请改为粘贴文字')),15000);})]);
 } catch(e) {
  if(e.name==='PasswordException') throw Error('PDF 有密码保护，请在本机解锁后重试');
  if(e.name==='InvalidPDFException') throw Error('PDF 无法读取，请检查文件或粘贴文字');
  throw e;
 } finally {clearTimeout(timer);await task.destroy();}
}
