export async function bootApplication({document,loadApp,reload,timeoutMs=20000}){
 const root=document.documentElement,status=document.getElementById('boot-status');let timer;
 try{await Promise.race([loadApp(),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('startup_timeout')),timeoutMs);})]);root.setAttribute('data-terrafar-boot','ready');status?.remove();return true;}
 catch{root.setAttribute('data-terrafar-boot','error');if(status){status.textContent='最新内容暂时无法加载，请检查网络后重试。未切换到旧版内容。';const retry=document.createElement('button');retry.type='button';retry.textContent='重新加载';retry.onclick=reload;status.append(retry);}return false;}
 finally{clearTimeout(timer);}
}
if(typeof document!=='undefined')void bootApplication({document,loadApp:()=>import('./radar.mjs?v=fresh-start-20261105'),reload:()=>location.reload()});
