import {effectiveDeadline,opportunityState} from './opportunity.mjs';
// A future deadline describes a saved advertisement, never proves a vacancy is open.
const DAY = 86400000;
function dayNumber(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const time = Date.parse(`${value}T00:00:00Z`);
  return Number.isFinite(time) && new Date(time).toISOString().slice(0, 10) === value ? time / DAY : null;
}

export function classifySnapshot(job, today = new Date().toISOString().slice(0, 10), fallbackCheckedAt = '') {
  const now = dayNumber(today);
  if (now === null) throw new TypeError('today must be a valid YYYY-MM-DD date');
  const deadline = dayNumber(effectiveDeadline(job));
  const checkedAt = job?.checkedAt || fallbackCheckedAt;
  const checked = dayNumber(checkedAt);
  const ageDays = checked === null || checked > now ? null : now - checked;
  const daysLeft = deadline === null ? null : deadline - now;
  let status = 'unknown', label = '截止日期待核实';
  if (daysLeft !== null) {
    if (daysLeft < 0) { status = 'past'; label = '快照截止日期已过'; }
    else if (daysLeft === 0) { status = 'today'; label = '快照显示今日截止'; }
    else if (daysLeft <= 7) { status = 'soon'; label = `快照显示 ${daysLeft} 天后截止`; }
    else { status = 'future'; label = '快照截止日期尚未到'; }
  }
  const freshness = ageDays === null ? 'unknown' : ageDays > 7 ? 'stale' : 'recent';
  const freshnessLabel = ageDays === null ? '核验日期待补充' : ageDays === 0 ? '今天核对过来源' : `${ageDays} 天前核对过来源`;
  return {status, label, daysLeft, checkedAt: ageDays === null ? null : checkedAt, ageDays, freshness, freshnessLabel,
    action: status === 'past' ? '查看原帖是否延期或有新一轮招聘' : status === 'today' || status === 'soon' ? '打开原帖确认当地截止时间及是否仍接受申请' : '打开原帖确认最新招聘状态',
    isVerifiedOpen: opportunityState(job,today).eligibleForOpenRecommendation};
}

export function canonicalSourceUrl(value) {
  try {
    const url = new URL(value);
    if (!['https:', 'http:'].includes(url.protocol) || url.username || url.password) return null;
    url.hash = '';
    for (const key of [...url.searchParams.keys()]) if (/^(utm_|mw_source$|gh_src$)/i.test(key)) url.searchParams.delete(key);
    url.searchParams.sort();
    // Keep job identifier query parameters, path case and scheme: aggressive normalization can merge distinct ads.
    return url.href;
  } catch { return null; }
}

export function summarizeCoverage(jobs, today = new Date().toISOString().slice(0, 10), fallbackCheckedAt = '') {
  const countries = Object.create(null), fields = Object.create(null), institutions = new Set(), urls = new Set();
  const statuses = {past: 0, today: 0, soon: 0, future: 0, unknown: 0};
  let duplicateUrls = 0, needsRecheck = 0;
  for (const job of jobs) {
    const quality = classifySnapshot(job, today, fallbackCheckedAt);
    statuses[quality.status]++;
    if (quality.freshness !== 'recent') needsRecheck++;
    countries[job.country || '地区未标注'] = (countries[job.country || '地区未标注'] || 0) + 1;
    fields[job.field || '领域未标注'] = (fields[job.field || '领域未标注'] || 0) + 1;
    if (job.institution) institutions.add(job.institution);
    const url = canonicalSourceUrl(job.url);
    if (url && urls.has(url)) duplicateUrls++;
    if (url) urls.add(url);
  }
  const countryCounts = Object.entries(countries).map(([name, count]) => ({name, count})).sort((a,b) => b.count-a.count || a.name.localeCompare(b.name));
  return {total: jobs.length, countries: countryCounts, fields, institutionCount: institutions.size, statuses, duplicateUrls, needsRecheck,
    note: jobs.length ? '数量为已收录公告数；同一公告多个名额只计一次。未收录不代表没有岗位。' : '当前还没有收录公告，可前往官方招聘入口继续查找。'};
}
