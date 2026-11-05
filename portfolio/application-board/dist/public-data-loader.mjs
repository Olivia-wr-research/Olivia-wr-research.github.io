// Public JSON is revalidated on every page open, never restored from personal storage.
export function validatePublicDataset(value){
 if(!value||value.format!=='terrafar-public-dataset-v1'||!Array.isArray(value.records)||!/^\d{4}-\d{2}-\d{2}$/.test(value.asOf||'')||! /^[a-f0-9]{64}$/.test(value.datasetSha256||''))throw Error('public_dataset_invalid');
 const ids=new Set();for(const row of value.records){if(!row||typeof row.id!=='string'||!row.id||ids.has(row.id))throw Error('public_dataset_invalid');ids.add(row.id);}
 return value;
}
export async function loadPublicDataset(url,{fetchImpl=globalThis.fetch,timeoutMs=15000}={}){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),timeoutMs);
 try{const response=await fetchImpl(url,{cache:'no-cache',credentials:'same-origin',redirect:'error',signal:controller.signal});if(!response.ok)throw Error('public_dataset_unavailable');return validatePublicDataset(await response.json());}
 finally{clearTimeout(timer);}
}
