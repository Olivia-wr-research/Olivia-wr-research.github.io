// Collection dates are not source publication dates or verification dates.
export function collectionDate(record){
 const value=record.collectedAt;
 if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value))return '';
 const date=new Date(value+'T00:00:00Z');
 return Number.isFinite(date.getTime())&&date.toISOString().slice(0,10)===value?value:'';
}
export function newestCollected(a,b){return collectionDate(b).localeCompare(collectionDate(a));}
export function setupCollectionSort(select){
 const option=document.createElement('option');option.value='newest';select.append(option);
 const update=()=>{const en=document.documentElement.lang==='en';option.textContent=en?'Recently added first':'最新收录优先';select.title=en?'Recently added uses catalogue collection dates, not official publication dates. Unknown dates come last.':'最新收录按本站收录日期排序，不代表官网刚发布；日期未知的项目排在后面。';};
 update();window.addEventListener('languagechange',update);
}
