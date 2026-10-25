"""Read the public ETH employer listing. No accounts, personal CVs or application submissions.

Run manually: python scripts/import_eth.py --output /path/to/review.json
Output is a review queue; it does not publish or overwrite the production dataset.
"""
import argparse, datetime, hashlib, html, json, re, time, subprocess
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlsplit

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
class _ListingParser(HTMLParser):
    """Account for every advertised card before applying the doctoral scope."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards=[];self.errors=[];self.advertised=0;self.current=None;self.stack=[]
    def finish(self,reason=None):
        item=self.current
        if item is None:return
        warnings=list(item['warnings'])
        if reason:warnings.append(reason)
        if any(tag=='h3' for tag,_ in self.stack):warnings.append('unclosed_title')
        title=re.sub(r'\s+',' ',' '.join(item['titleEn'])).strip()
        raw=item['href'];url='';parsed=None
        try:url=urljoin(BASE,raw);parsed=urlsplit(url)
        except ValueError:pass
        usable_url=parsed is not None and bool(raw) and not raw.startswith('#') and parsed.scheme=='https' and parsed.netloc=='jobs.ethz.ch' and parsed.path not in ('','/') and not item['ambiguous_href']
        if not title:warnings.append('missing_title')
        if not usable_url:warnings.append('missing_or_unsafe_detail_url')
        warnings=list(dict.fromkeys(warnings))
        if warnings:self.errors.append({'card_index':item['index'],'reason':warnings[0],'reasons':warnings,'title':title,'href':raw})
        # Structural damage prevents a complete scope, but an already discovered
        # title/URL remains a review candidate instead of silently disappearing.
        if title and usable_url:
            card={'titleEn':title,'url':url,**{key:re.sub(r'\s+',' ',' '.join(item[key])).strip() for key in ('listingDetails','listingDepartment')}}
            if warnings:card['listingParseWarnings']=warnings
            self.cards.append(card)
        self.current=None;self.stack=[]
    def handle_starttag(self,tag,attrs):
        attribute_pairs=attrs
        classes=[token for name,value in attribute_pairs if name=='class' for token in (value or '').split()]
        attrs=dict(attribute_pairs)
        if tag=='a':
            if self.current is not None:self.finish('nested_anchor_in_card')
            if 'job-ad__item__link' in classes:
                self.advertised+=1
                duplicate_attrs=[name for name in ('class','href') if sum(key==name for key,_ in attribute_pairs)>1]
                self.current={'index':self.advertised,'href':(attrs.get('href') or '').strip(),'titleEn':[],'listingDetails':[],'listingDepartment':[],
                              'warnings':['duplicate_card_attribute'] if duplicate_attrs else [],'ambiguous_href':len({value for key,value in attribute_pairs if key=='href'})>1}
        if self.current is None:return
        if tag not in ('span','b','em','strong','i','small','sup','sub','abbr','br','wbr'):
            for i,(parent,_) in enumerate(self.stack):
                if parent=='h3':
                    self.current['warnings'].append('unclosed_title');self.stack=self.stack[:i];break
        field='titleEn' if tag=='h3' else 'listingDetails' if 'job-ad__item__details' in classes else 'listingDepartment' if 'job-ad__item__company' in classes else None
        if tag not in ('br','img','input','hr','meta','link','wbr','source','area','base','col','embed','param','track'):
            self.stack.append((tag,field))
    def handle_endtag(self,tag):
        if self.current is None:return
        if tag=='a':self.finish();return
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:
                self.stack=self.stack[:i];break
    def handle_data(self,data):
        if self.current is None:return
        for _,field in reversed(self.stack):
            if field:
                self.current[field].append(data);break

def parse_listing_cards(body):
    parser=_ListingParser();parser.feed(body);parser.close()
    if parser.current is not None:parser.finish('unclosed_card')
    return {'advertised_cards':parser.advertised,'cards':parser.cards,'errors':parser.errors}

def parse_listing(body):
    found=[row for row in parse_listing_cards(body)['cards'] if doctoral(row['titleEn'])]
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
