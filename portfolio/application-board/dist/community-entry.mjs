// Core details use addressable pages; only lightweight feedback stays modal.
import {openFeedbackForm} from './feedback-link.mjs';
if(typeof document!=='undefined'){
 const openFeedback=openFeedbackForm;
 const nav=document.querySelector('header nav');if(nav){const b=document.createElement('button');b.textContent='反馈';b.onclick=()=>openFeedback();nav.append(b);}
 document.addEventListener('click',e=>{if(e.target.closest?.('#groups-tab,#groups-start')){e.preventDefault();e.stopImmediatePropagation();window.dispatchEvent(new Event('terrafar-researchers'));return;}const a=e.target.closest?.('a[href]');if(!a)return;const u=new URL(a.href,location.href);if(u.origin!==location.origin)return;if(u.pathname.endsWith('/feedback.html')){e.preventDefault();openFeedback(u.searchParams.get('object')||'');}if(u.pathname.endsWith('/mentor.html')){e.preventDefault();window.dispatchEvent(new Event('terrafar-researchers'));}},true);
 const q=new URLSearchParams(location.search);if(q.get('panel')==='feedback')openFeedback(q.get('object')||'');
}
