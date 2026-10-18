// Local-only cartographic assets: Natural Earth (public domain).
// Country label points are approximate, never employer or user locations.
const aliases = { '中国': 'China', '中国大陆': 'China', '美国': 'United States of America', 'USA': 'United States of America', 'US': 'United States of America', 'UK': 'United Kingdom', 'Czech Republic': 'Czechia', '捷克': 'Czechia', '韩国': 'South Korea' };
const normalized = value => String(value || '').trim().toLowerCase();
export function countryIndex(geojson) {
  const index = new Map();
  for (const feature of geojson.features || []) {
    const p = feature.properties || {};
    for (const key of ['ADMIN', 'NAME', 'NAME_LONG', 'NAME_EN', 'NAME_ZH', 'ISO_A2', 'ISO_A3']) {
      if (p[key] && p[key] !== '-99') index.set(normalized(p[key]), feature);
    }
  }
  for (const [alias, original] of Object.entries(aliases)) {
    const feature = index.get(normalized(original));
    if (feature) index.set(normalized(alias), feature);
  }
  return index;
}
export function groupMapRows(rows, index) {
  const groups = new Map();
  const unmapped = [];
  for (const row of rows) {
    const feature = index.get(normalized(row.country)) || index.get(normalized(row.countryEn));
    const p = feature?.properties;
    if (!p || !Number.isFinite(p.LABEL_X) || !Number.isFinite(p.LABEL_Y)) { unmapped.push(row); continue; }
    const key = p.ADMIN || p.NAME;
    if (!groups.has(key)) groups.set(key, { key, country: row.country || row.countryEn, name: p.NAME_ZH || key, nameEn: key, coordinates: [p.LABEL_Y, p.LABEL_X], rows: [] });
    groups.get(key).rows.push(row);
  }
  return { groups: [...groups.values()], unmapped };
}
function stylesheet(file) {
  const href = new URL(file, import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement('link'); link.rel = 'stylesheet'; link.href = href; document.head.append(link);
  }
}
// Orthographic globe, rendered entirely from local Natural Earth geometries.
const DEG=Math.PI/180;
export function projectGlobe(lat,lon,centreLat=20,centreLon=10){
 const p=lat*DEG,d=(lon-centreLon)*DEG,c=centreLat*DEG;
 return {x:Math.cos(p)*Math.sin(d),y:Math.cos(c)*Math.sin(p)-Math.sin(c)*Math.cos(p)*Math.cos(d),visible:Math.sin(c)*Math.sin(p)+Math.cos(c)*Math.cos(p)*Math.cos(d)>0};
}
function element(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
export async function setupGeographyMap(container,{onSelect=()=>{},onCountry=()=>{}}={}){
 stylesheet('./geography-map.css');
 const response=await fetch(new URL('./vendor/world-110m.geojson',import.meta.url));if(!response.ok)throw Error('Local geography data could not load');
 const world=await response.json(),index=countryIndex(world);
 container.classList.add('geography-explorer');container.replaceChildren();
 const shell=element('div','geo-earth-shell'),visual=element('div','geo-earth-visual'),canvas=element('canvas','geo-globe');
 canvas.width=560;canvas.height=560;canvas.tabIndex=0;canvas.setAttribute('role','img');
 const ctx=canvas.getContext('2d');if(!ctx)throw Error('Canvas unavailable');
 visual.append(canvas,element('span','geo-projection-label','ORTHOGRAPHIC · NATURAL EARTH'));
 const side=element('div','geo-earth-side'),title=element('h3'),hint=element('p','geo-earth-hint'),views=element('div','geo-region-views'),selection=element('div','geo-map-selection');
 selection.hidden=true;selection.setAttribute('aria-live','polite');
 const caption=element('p','geo-map-caption'),countries=element('div','geo-country-buttons'),credit=element('a','geo-map-credit','Natural Earth · Public domain');
 credit.href='https://www.naturalearthdata.com/about/terms-of-use/';credit.target='_blank';credit.rel='noopener noreferrer';
 side.append(element('span','geo-earth-kicker','A FIELD GUIDE TO YOUR NEXT CHAPTER'),title,hint,views,selection,caption,credit);shell.append(visual,side);container.append(shell,countries);
 const options=[['欧洲','Europe',48,12],['美洲','Americas',18,-90],['亚洲','Asia',25,105],['大洋洲','Oceania',-25,145],['非洲','Africa',5,20]];
 let centreLat=25,centreLon=15,groups=[],english=false,frame=0,drag,selected;
 const buttons=options.map(([zh,en,lat,lon])=>{const b=element('button','',zh);b.type='button';b.onclick=()=>{centreLat=lat;centreLon=lon;schedule();};views.append(b);return b;});
 const texture=document.createElement('canvas');texture.width=1440;texture.height=720;
 const tx=texture.getContext('2d',{willReadFrequently:true});let pixels;
 function makeTexture(){
  tx.fillStyle='#0965ce';tx.fillRect(0,0,1440,720);const represented=new Set(groups.map(g=>g.key));
  for(const feature of world.features){
   const polys=feature.geometry.type==='MultiPolygon'?feature.geometry.coordinates:[feature.geometry.coordinates];tx.beginPath();
   for(const polygon of polys)for(const ring of polygon){ring.forEach(([lon,lat],i)=>{const x=(lon+180)*4,y=(90-lat)*4;if(i===0)tx.moveTo(x,y);else tx.lineTo(x,y);});tx.closePath();}
   tx.fillStyle=represented.has(feature.properties.ADMIN||feature.properties.NAME)?'#99b298':'#5f826a';tx.fill('evenodd');tx.lineWidth=.6;tx.strokeStyle='#c8d9bf55';tx.stroke();
  }
  tx.strokeStyle='#c3ddff22';tx.lineWidth=.8;tx.beginPath();
  for(let lon=-180;lon<=180;lon+=30){tx.moveTo((lon+180)*4,0);tx.lineTo((lon+180)*4,720);}
  for(let lat=-60;lat<=60;lat+=30){tx.moveTo(0,(90-lat)*4);tx.lineTo(1440,(90-lat)*4);}
  tx.stroke();pixels=tx.getImageData(0,0,1440,720).data;
 }
 const radius=250,mid=280;
 function draw(){
  frame=0;const img=ctx.createImageData(560,560),out=img.data,c=centreLat*DEG;
  for(let sy=30;sy<530;sy++)for(let sx=30;sx<530;sx++){
   const x=(sx-mid)/radius,y=(mid-sy)/radius,r2=x*x+y*y;if(r2>1)continue;
   const z=Math.sqrt(1-r2),lat=Math.asin(z*Math.sin(c)+y*Math.cos(c));
   let lon=centreLon*DEG+Math.atan2(x,z*Math.cos(c)-y*Math.sin(c));lon=((lon/DEG+540)%360)-180;
   const px=Math.min(1439,Math.max(0,Math.floor((lon+180)*4))),py=Math.min(719,Math.max(0,Math.floor((90-lat/DEG)*4)));
   const source=(py*1440+px)*4,dest=(sy*560+sx)*4,light=.6+.4*Math.max(0,z*.78-x*.28+y*.22);
   out[dest]=pixels[source]*light;out[dest+1]=pixels[source+1]*light;out[dest+2]=pixels[source+2]*light;out[dest+3]=Math.min(255,(1-r2)*radius*255);
  }
  ctx.clearRect(0,0,560,560);ctx.putImageData(img,0,0);
  ctx.beginPath();ctx.arc(mid,mid,radius,0,Math.PI*2);ctx.strokeStyle='#a5d8ff99';ctx.lineWidth=1;ctx.stroke();
  for(const group of groups){const p=projectGlobe(...group.coordinates,centreLat,centreLon);if(!p.visible)continue;const x=mid+p.x*radius,y=mid-p.y*radius;
   ctx.beginPath();ctx.arc(x,y,3.8,0,Math.PI*2);ctx.fillStyle='#f4e3b4';ctx.fill();ctx.strokeStyle='#123e77';ctx.lineWidth=1.5;ctx.stroke();
   if(group===selected){ctx.beginPath();ctx.arc(x,y,8,0,Math.PI*2);ctx.strokeStyle='#fff3ce';ctx.lineWidth=1;ctx.stroke();}
  }
 }
 function schedule(){if(!frame)frame=requestAnimationFrame(draw);}
 function select(group){
  selected=group;centreLat=group.coordinates[0];centreLon=group.coordinates[1];schedule();selection.hidden=false;selection.replaceChildren();
  selection.append(element('strong','',(english?group.nameEn:group.name)+' · '+group.rows.length));
  const filter=element('button','geo-popup-filter',english?'Explore this destination →':'查看这个目的地 →');filter.type='button';filter.onclick=()=>onCountry(group.country);selection.append(filter);
  for(const row of group.rows.slice(0,2)){const b=element('button','geo-popup-job',english?row.titleEn||row.title:row.title||row.titleEn);b.type='button';b.onclick=()=>onSelect(row.id);selection.append(b);}
 }
 canvas.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,lat:centreLat,lon:centreLon,moved:false};canvas.setPointerCapture(e.pointerId);});
 canvas.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.abs(dx)+Math.abs(dy)>4)drag.moved=true;centreLon=drag.lon-dx*.4;centreLat=Math.max(-80,Math.min(80,drag.lat+dy*.3));schedule();});
 canvas.addEventListener('pointerup',e=>{
  if(drag&&!drag.moved){const b=canvas.getBoundingClientRect(),x=(e.clientX-b.left)*560/b.width,y=(e.clientY-b.top)*560/b.height;let nearest,d=22;
   for(const g of groups){const p=projectGlobe(...g.coordinates,centreLat,centreLon),dist=Math.hypot(x-mid-p.x*radius,y-mid+p.y*radius);if(p.visible&&dist<d){nearest=g;d=dist;}}if(nearest)select(nearest);
  }drag=null;
 });
 canvas.addEventListener('pointercancel',()=>{drag=null;});
 canvas.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home'].includes(e.key))return;e.preventDefault();
  if(e.key==='Home'){centreLat=25;centreLon=15;}else{centreLon+=e.key==='ArrowLeft'?-15:e.key==='ArrowRight'?15:0;centreLat=Math.max(-80,Math.min(80,centreLat+(e.key==='ArrowUp'?10:e.key==='ArrowDown'?-10:0)));}schedule();
 });
 function update(rows,language='zh'){
  english=language==='en';const result=groupMapRows(rows,index);groups=result.groups;selected=undefined;selection.hidden=true;
  title.textContent=english?'One planet. Many next chapters.':'以世界为坐标，寻找下一站。';
  hint.textContent=english?'Drag to explore the globe, or choose a destination below.':'拖动地球，看看世界的另一面。也可以直接选择下方的目的地。';
  canvas.setAttribute('aria-label',english?'Rotatable orthographic globe. Arrow keys rotate; Home resets. Country buttons below.':'可旋转正射地球。方向键旋转，Home键复位；下方提供国家按钮。');
  buttons.forEach((b,i)=>{b.textContent=options[i][english?1:0];});
  caption.textContent=english?groups.length+' destinations. Country-level points, not campuses. Illustrative boundaries.'+(result.unmapped.length?' '+result.unmapped.length+' unmapped records remain in the list.':''):groups.length+' 个目的地。点位代表国家级概略位置，不是校园；边界仅作示意。'+(result.unmapped.length?result.unmapped.length+' 条未定位记录仍保留在列表。':'');
  countries.replaceChildren();for(const group of groups){const b=element('button','geo-country-chip',(english?group.nameEn:group.name)+' · '+group.rows.length);b.type='button';b.onclick=()=>{select(group);onCountry(group.country);};countries.append(b);}makeTexture();schedule();
 }
 update([]);
 return {update,invalidate:schedule,destroy:()=>{if(frame)cancelAnimationFrame(frame);container.replaceChildren();}};
}
