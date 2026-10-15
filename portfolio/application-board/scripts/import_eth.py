"""Read the public ETH employer listing. No accounts, personal CVs or application submissions.

Run manually: python scripts/import_eth.py --output /path/to/review.json
Output is a review queue; it does not publish or overwrite the production dataset.
"""
import argparse, datetime, hashlib, html, json, re, time, subprocess
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.parse import urljoin

BASE='https://jobs.ethz.ch/'
def fetch(url):
    if not url.startswith(BASE):raise ValueError('Unexpected source host')
    result=subprocess.run(['curl','-L','--fail','--max-time','25','-sS','--user-agent','NextPositionSourceReview/0.6',url],capture_output=True,check=True)
    if len(result.stdout)>3000000:raise ValueError('Response too large')
    return result.stdout.decode('utf-8')
def clean(value):
    return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',value))).strip()
def doctoral(title):
    return bool(re.search(r'\bph\.?d\b|doctoral|doktorand',title,re.I)) and not re.search(r'post.?doc|postdoctoral',title,re.I)
def parse_listing(body):
    found=[]
    for block in re.findall(r'<a\b[^>]*class="job-ad__item__link"[\s\S]*?</a>',body):
        title=re.search(r'<h3[^>]*>([\s\S]*?)</h3>',block)
        if not title or not doctoral(clean(title[1])):continue
        href=re.search(r'href="([^"]+)"',block)
        detail=re.search(r'class="job-ad__item__details">([\s\S]*?)</div>',block)
        company=re.search(r'class="job-ad__item__company">([\s\S]*?)</div>',block)
        if href:found.append({'titleEn':clean(title[1]),'url':urljoin(BASE,html.unescape(href[1])),'listingDetails':clean(detail[1]) if detail else '', 'listingDepartment':clean(company[1]) if company else ''})
    return list({x['url']:x for x in found}.values())
def sections(body):
    start=body.find('<!-- JOB DESCRIPTION -->')
    if start>=0:body=body[start:]
    parts=re.split(r'<h2[^>]*>([\s\S]*?)</h2>',body)
    return {clean(parts[i]).lower():clean(parts[i+1]) for i in range(1,len(parts)-1,2)}
def excerpt(text,limit=420):
    # Do not distribute contacts or raw HTML. Keep a short original-language extract.
    text=re.sub(r'\S+@\S+','',text)
    return text[:limit].rsplit(' ',1)[0]+('…' if len(text)>limit else '')
def record(item,body,checked):
    parts=sections(body);title=item['titleEn'];detail=item['listingDetails'];text=' '.join([title,*parts.values()]);low=text.lower()
    topics=[];methods=[]
    for label,words in [('人工智能',['artificial intelligence','machine learning']),('环境',['environment','ecology']),('材料科学',['material']),('物理学',['physics','quantum']),('生物医学',['biology','biological','biomedical','biomolecular']),('能源',['energy']),('计算机科学',['computer science','computing','software']),('经济学',['economics','economic'])]:
        if any(w in low for w in words):topics.append(label)
    for label,words in [('Python',['python']),('R',[' r,',' r.',' r ']),('机器学习',['machine learning']),('实验',['experiment']),('统计',['statistic']),('数据分析',['data analysis']),('数学优化',['optimization','optimisation']),('网络分析',['network analysis'])]:
        if any(w in low for w in words):methods.append(label)
    field='跨学科研究'
    for label,words in [('生命科学与健康',['biology','biomedical','health','neuro','molecular']),('人工智能与计算',['learning','computing','computer','ai ','intelligence']),('环境与地球科学',['climate','environment','earth','geophys','forest']),('工程与能源',['robot','engineer','energy','mechanic','electr']),('数学与物理',['quantum','physics','mathemat','topolog'])]:
        if any(w in title.lower() for w in words):field=label;break
    return dict(id='eth-'+hashlib.sha256(item['url'].encode()).hexdigest()[:12],title=title,titleEn=title,institution='苏黎世联邦理工学院',institutionEn='ETH Zürich',short='ETH',country='新加坡' if 'singapore' in detail.lower() else '瑞士',countryEn='Singapore' if 'singapore' in detail.lower() else 'Switzerland',city=detail.split(',')[1].strip() if ',' in detail else '',field=field,topics=topics,methods=methods,degree='unknown',language='具体语言要求见招聘详情',languageEn='See the employer requirements',funding='博士研究岗位',fundingEn='Doctoral research position',salary='薪资与合同请查看招聘详情',salaryEn='See employer salary and contract terms',deadline='',summary='研究方向：'+title,summaryEn=excerpt(parts.get('project background',parts.get('job description',''))),requirements='请在下方英文招聘要求中查看专业、方法与学位条件。',requirementsEn=excerpt(parts.get('profile',''),650),caution='具体截止日期与申请条件请查看招聘方页面。',cautionEn='Check the employer page for the closing date and full application conditions.',url=item['url'],checkedAt=checked,sourceId='eth',sourceTitle=title,sourceExcerpt=excerpt(parts.get('project background',parts.get('job description','')),350),sourceRequirements=excerpt(parts.get('profile',''),500),listingDetails=detail,contentHash=hashlib.sha256(body.encode()).hexdigest(),retrievalStatus='listed',translationStatus='original-title')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    today=datetime.date.today().isoformat();items=parse_listing(fetch(BASE));rows=[];errors=[]
    for item in items:
        try:rows.append(record(item,fetch(item['url']),today))
        except Exception as error:errors.append({'url':item['url'],'error':type(error).__name__})
        time.sleep(.35)
    from pathlib import Path
    target=Path(args.output)
    if target.exists():raise SystemExit('Refusing to overwrite existing review output')
    target.write_text(json.dumps({'source':BASE,'checkedAt':today,'records':rows,'errors':errors},ensure_ascii=False,indent=2))
    print(json.dumps({'records':len(rows),'errors':len(errors),'output':str(target)}))
if __name__=='__main__':main()
