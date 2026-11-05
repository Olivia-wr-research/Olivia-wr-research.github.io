// User-facing day boundaries are explicit; source deadline times are never inferred.
export const DISPLAY_TIME_ZONE='Asia/Shanghai';
export function calendarDate(at=new Date()){
 const date=at instanceof Date?at:new Date(at);
 if(!Number.isFinite(date.getTime()))throw new TypeError('Invalid calendar date');
 const parts=new Intl.DateTimeFormat('en-CA',{timeZone:DISPLAY_TIME_ZONE,year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(date);
 const value=type=>parts.find(p=>p.type===type).value;
 return `${value('year')}-${value('month')}-${value('day')}`;
}
