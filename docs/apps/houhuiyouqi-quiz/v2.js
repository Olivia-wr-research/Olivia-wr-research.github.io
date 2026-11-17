'use strict';
/* Fan creative work. Scenes are grounded in published episode titles; character profiles are game archetypes, not assessments of cast members. */
const APP_PATH='https://olivia-wr-research.github.io/apps/houhuiyouqi-quiz/';
const EPISODE='https://www.mgtv.com/h/914227.html';
const EVIDENCE='https://www.mgtv.com/act/2026/hhyq2026/';
const templates=[
{id:'cinema',name:'A · 公路电影',desc:'故事感与电影感'},
{id:'ticket',name:'B · 友情车票',desc:'一张不退票的关系单'},
{id:'magazine',name:'C · 友情人物特刊',desc:'人设像杂志封面'},
{id:'danmu',name:'D · 弹幕破防卡',desc:'适合朋友圈互相贴脸'}];
const photoSources={
ma:{url:'https://commons.wikimedia.org/wiki/Special:FilePath/180115%20%E8%8B%B1%E9%9B%84%E6%9C%AC%E8%89%B22018%20%E9%A6%96%E6%98%A0%E7%A4%BC%20%E7%BA%A2%E6%AF%AF%20%E9%A9%AC%E5%A4%A9%E5%AE%87%206.jpg?width=850',credit:'RayOfSunshine · CC BY 2.5 · 马天宇红毯照片（海报裁剪排版）',source:'https://commons.wikimedia.org/wiki/Category:Ma_Tianyu_in_2018'},
zhang:{url:'https://commons.wikimedia.org/wiki/Special:FilePath/Alina%20Zhang%20Meng%20cropped.jpg?width=850',credit:'rayofsunshine · CC BY 2.5 · 张萌人物照片（原图已裁剪，海报再次排版）',source:'https://commons.wikimedia.org/wiki/File:Alina_Zhang_Meng_cropped.jpg'}};
const characters=[
{id:'li',name:'厉娜',title:'友情「已读但不强制原谅」派',stamp:'不和好也可以是结局',meme:'别人：都这么久了，你还不翻篇？\n你：日历会自动翻页，关系又不是自动续费。',caption:'表面：没什么好说的。\n心里：发生过的事，不会因为时间久就变成没发生。',touch:'你不是把旧事记成账本，而是知道有些伤口不能靠一句“算了吧”解决。你可以允许对方把话说完，也允许自己保留感受。对你来说，体面的告别和重新开始一样值得尊重。',weak:'太习惯自己消化情绪，别人可能不知道你真的有多难过。',mission:'你的友情通关提示：不必为了证明大度，把还没愈合的事轻轻带过。',scenetitle:'节目对应：厉娜与许飞车上对谈，以及“不一定继续做朋友”的表达',scenesrc:EVIDENCE,pair:'许飞',tags:['边界先于和解','慢热但记得','可以体面告别'],dims:[24,80,29,34,40],theme:'#748b95'},
{id:'xu',name:'许飞',title:'友情「往事售后客服」派',stamp:'工单可以关闭，话要说完',meme:'别人：都过去十几年了。\n你：时间是过去了，我的未读消息还没处理。',caption:'嘴上：都过去了。\n脑内：那段友情的复盘文档已自动打开第18版。',touch:'你在意的不是赢一场争论，而是想知道两个人为什么从亲近走到了这里。你愿意翻开旧信，也愿意试着把没说完的话讲出来。但你慢慢会明白：表达你的版本很重要，接受对方未必给你同一种答案也很重要。',weak:'你有时候把“说清楚”误当成“还能回到从前”。',mission:'你的友情通关提示：说完想说的话，就已经完成了自己的那一部分。',scenetitle:'节目对应：许飞读介绍信落泪、与厉娜谈过往及询问能否重新做朋友',scenesrc:EVIDENCE,pair:'厉娜',tags:['未完待续型','复盘十级学者','情感存档'],dims:[83,38,62,50,58],theme:'#7b9b91'},
{id:'zhang',name:'张萌',title:'友情「删了微信也要送杯子」派',stamp:'朋友可以断联，礼物不能缺席',meme:'别人：都断联了还买礼物？\n你：好友可以不在列表，但还在我的购物灵感里。',caption:'嘴上：没关系，不联系就算了。\n购物车：这杯子TA应该会喜欢。',touch:'你是那种看到一个小物件就会突然想到某个旧友的人。对你来说，关系不是一道非黑即白的选择题。你愿意主动靠近，也容易在热情里忘记：对方或许还没有准备好。你的勇敢很珍贵，尊重对方的节奏也很重要。',weak:'好意跑得比沟通快，偶尔会变成别人感受到的压力。',mission:'你的友情通关提示：送礼物之前，先确认对方愿不愿意重新打开那扇门。',scenetitle:'节目对应：张萌提到断联期间仍记得马天宇喜欢收藏马克杯',scenesrc:EPISODE,pair:'马天宇',tags:['礼物记忆王','主动发起重联','热心但容易超速'],dims:[95,38,83,86,57],theme:'#c58e71'},
{id:'ma',name:'马天宇',title:'友情「边界感保安队长」派',stamp:'请先刷卡，再进我的舒适区',meme:'别人：我们关系这么好，你还分什么边界？\n你：好朋友也得敲门，门禁不是装饰。',caption:'表面：我只想自己待会儿。\n真心：我很珍惜你，但我不能把所有空间都交出去。',touch:'你喜欢的是彼此尊重、允许各自独处的关系。对方太急于替你安排时，你会迅速感到疲惫。你不一定少情，也不一定冷淡；你只是更相信，长久的亲密应该留得下自由活动的空间。',weak:'你习惯用退后表示不舒服，别人可能根本没有收到通知。',mission:'你的友情通关提示：边界明确很酷，偶尔解释清楚会更省力。',scenetitle:'节目对应：马天宇谈享受独处，并就张萌的相处方式表达边界感',scenesrc:EVIDENCE,pair:'张萌',tags:['独处是刚需','越界提醒器','尊重双向选择'],dims:[32,96,53,37,27],theme:'#819eaf'},
{id:'wen',name:'文吉儿',title:'友情「唯一好友单推人」派',stamp:'我不是要绑住你，只想确定我很重要',meme:'别人：朋友又不是单选题。\n你：我知道啊，我只是想当那道压轴大题。',caption:'嘴上：你交新朋友没关系。\n心里：那我们的专属默契，还有没有名字？',touch:'你能接受朋友拥有自己的世界，却很在意某种只有彼此才懂的连接是否还存在。你会记住过去的承诺，也会敏锐地察觉关系的微小变化。你想要的并不是控制，而是一份被认真放在心上的确定感。',weak:'当亲密的定义不一样时，你可能把对方的自由误读成自己不够重要。',mission:'你的友情通关提示：与其猜自己是不是唯一，不如说出你真正想被怎样对待。',scenetitle:'节目对应：文吉儿与王子璇对好友“唯一性”的期待差异',scenesrc:EPISODE,pair:'王子璇',tags:['友情单推','需要确定感','记得每次偏爱'],dims:[69,28,48,35,99],theme:'#bc8c9d'},
{id:'wang',name:'王子璇',title:'友情「好友列表非单选」派',stamp:'亲密不是独占，真诚才是必选',meme:'别人：我是你唯一的朋友吗？\n你：你是重要的人，但我的通讯录不参加排他赛。',caption:'表面：大家都能好好相处。\n心里：为什么我交新朋友，也需要交一份解释报告？',touch:'你珍惜亲密，也看重相处中的选择空间。对你来说，友谊不是占有权证明，而是各自都能自然做自己。可当对方特别需要确定感时，你的轻松可能被听成疏远；你也需要学会把“重要”说得更具体。',weak:'过分相信“对方应该懂”，往往让沉默变成了误解。',mission:'你的友情通关提示：自由是底色，让对方感到被珍惜也并不矛盾。',scenetitle:'节目对应：王子璇与文吉儿围绕朋友关系及亲密期待的讨论',scenesrc:EPISODE,pair:'文吉儿',tags:['社交不锁区','沟通不猜谜','重要不等于唯一'],dims:[43,83,83,51,34],theme:'#c1aa8d'},
{id:'qing',name:'青稚',title:'友情「前队友复活赛」派',stamp:'你先别退队，我们再打一次',meme:'别人：都不是队友了，还惦记呢？\n你：战队能换，老搭档的默契哪有一键卸载。',caption:'嘴上：大家各走各的路。\n身体：对方有事，我先冲过去。',touch:'你很重视并肩作战积累出来的默契，所以当合作变了味，你往往比别人更难受。你可能嘴硬、可能急着争个结果，但心里其实还希望彼此能再次好好配合。有些关系不是不重要，而是你们还没学会用同一种速度沟通。',weak:'你太想立刻推进局面，反而可能让需要冷静的人更想后退。',mission:'你的友情通关提示：想重组一支队伍，第一步也许不是冲锋，而是听清对方想去哪。',scenetitle:'节目对应：青稚白小纯领队意见不合、旅行中落泪与尝试重新同行',scenesrc:EVIDENCE,pair:'白小纯',tags:['前队友滤镜','行动快过嘴','嘴硬心软'],dims:[84,33,51,97,81],theme:'#aa9069'},
{id:'bai',name:'白小纯',title:'友情「先对线后搬行李」派',stamp:'道理要讲，忙也能帮',meme:'别人：你俩不是吵架了吗？\n你：吵归吵，行李那么重，手也不能闲着啊。',caption:'表面：这件事我有我的观点。\n真心：但我也没说不在乎你。',touch:'你不是遇事会轻易低头的人，讲道理、保留立场对你很重要。可这不妨碍你在具体的事上伸手帮忙。你知道关系的复杂就在这里：情绪可以拧巴，行动里却仍然留着温度。',weak:'当你太在意把事情讲对，别人可能只听到了你的态度，没有看到你的关心。',mission:'你的友情通关提示：观点可以先放桌上，心意也值得被对方看见。',scenetitle:'节目对应：白小纯与青稚争执后仍帮忙搬行李、邀请回屋',scenesrc:EVIDENCE,pair:'青稚',tags:['行动派嘴替','不服软但会帮忙','理性热心混合体'],dims:[39,79,92,79,30],theme:'#7ca4a2'}
];
const C=Object.fromEntries(characters.map(c=>[c.id,c]));
/* All questions are newly written scenarios inspired by documented show moments; the options are not attributed to real cast members. */
const Q=[
{scene:'01 / 马克杯事件',fact:'节目相关情境：张萌提到断联期间还会想起马天宇喜欢的马克杯。',title:'和旧友断联多年，你刷到了一个TA绝对会喜欢的杯子。你的第一反应？',opts:[
['先加入购物车。有没有好友位不重要，我记得TA会喜欢。',[2,-1,1,2,1]],
['手指悬在分享键上三秒，最后划走。',[0,1,-1,-1,0]],
['买给自己。过去的审美可以保留，人不必回头。',[-2,2,-1,0,-1]],
['截图存着，下次有机会再把这件事讲明白。',[2,0,1,0,1]]]},
{scene:'02 / 同框零沟通',fact:'节目相关情境：厉娜和许飞曾被拍到面对面却没有交流。',title:'十八天旅程第一天，你和十年没联系的旧友被安排坐同一排。你会？',opts:[
['先主动打个招呼。社死也比一路装不认识好。',[2,-1,2,2,0]],
['戴上耳机，看风景。先不强求任何人。',[-2,2,-1,-1,-1]],
['等TA先开口，心里已经排练了八种开场白。',[1,-1,-1,0,2]],
['开门见山：“那件事，咱们要聊吗？”',[1,1,2,1,0]]]},
{scene:'03 / 关系越界预警',fact:'节目相关情境：马天宇谈到自己享受独处，也曾表达对相处越界的不适。',title:'关系很好的朋友未经商量，就把你安排进一个“惊喜重逢局”。你内心弹幕是？',opts:[
['“你是真的想见我？那咱们可以好好聊。”',[2,-1,2,1,1]],
['“我的社交日程不是盲盒，请先征求本人意见。”',[-1,2,2,0,-1]],
['“现在立刻取消，我需要一点自己的空间。”',[-2,2,0,-1,-1]],
['“来都来了，先看看能不能把局面救回来。”',[1,0,1,2,1]]]},
{scene:'04 / 友情唯一性考核',fact:'节目相关情境：文吉儿与王子璇谈到对朋友亲密关系的不同期待。',title:'最要好的朋友带来了新朋友，还说“以后咱们三个一起玩”。你会？',opts:[
['高兴加入！热闹一点也没什么不好。',[1,-1,1,2,-2]],
['笑着点头，回家开始思考“我们还是不是特别的？”',[0,-1,-1,0,2]],
['没问题，我的朋友不是单选题。',[-1,2,0,0,-2]],
['直说：“我不反对，只是有点担心我们的默契变了。”',[1,0,2,0,2]]]},
{scene:'05 / 领队意见不合',fact:'节目相关情境：青稚和白小纯曾因旅行安排出现分歧。',title:'两位曾经超有默契的搭档，现在连路线都讨论不拢。你是其中一个，你会？',opts:[
['“先走起来吧，路上总能找到办法。”',[1,-1,0,2,1]],
['“问题不在路，在我们有没有好好听对方说。”',[2,0,2,0,1]],
['“各走各的吧，强行组队容易再次翻车。”',[-2,2,0,-1,-2]],
['“先把分工、边界和规则谈清楚。”',[0,2,2,1,-1]]]},
{scene:'06 / 裹毯子落泪与搬行李',fact:'节目相关情境：青稚与白小纯经历争执，也有帮忙搬行李的互动。',title:'刚吵完一架，TA却默默帮你把行李搬回房间。你的第一句是？',opts:[
['“……谢谢。其实我也不想弄成这样。”',[2,-1,1,2,2]],
['“谢谢你，但那件事我们确实还没谈妥。”',[0,2,2,1,0]],
['“你别这样，我现在真的需要冷静一下。”',[-1,2,-1,-2,0]],
['先把水递给TA，话不必现在就说完。',[1,0,-1,1,1]]]},
{scene:'07 / 迟到的介绍信',fact:'节目相关情境：许飞读厉娜介绍信时落泪，旧事再次被谈起。',title:'一位旧友给你写了一封很长的信，几乎把过去都写进去了。你会？',opts:[
['认真读完，也写下自己的版本。',[2,0,2,0,1]],
['很感动，但“感动”和“原谅”是两件事。',[-1,2,1,0,-1]],
['先不回复，我需要自己把心情安顿好。',[-1,1,-2,-1,0]],
['直接约TA坐下来，一次把话讲清楚。',[2,-1,2,2,1]]]},
{scene:'08 / 观察室提问：满分还是零分',fact:'节目相关情境：观察嘉宾曾讨论“满分朋友”和“零分朋友”。',title:'观察室问：一段友情曾经100分，现在可能只剩10分。你认同哪个说法？',opts:[
['至少曾经100分，不会因为现在的10分就抹掉。',[1,-1,0,0,2]],
['过去是过去，今天怎么相处就按今天算。',[-2,2,0,0,-2]],
['分数不重要，先弄明白为什么走到了这一步。',[2,0,2,0,1]],
['别打分了，先给关系安排一次重新体验。',[2,-1,1,2,0]]]},
{scene:'09 / 狼人杀同桌局',fact:'节目相关情境：节目曾播出五人狼人杀游戏片段。',title:'狼人杀同桌偏偏坐着你曾经闹翻的那个人。TA说“信我”。你会？',opts:[
['这游戏先别带私人恩怨，认真玩完。',[0,1,1,1,-1]],
['“你说信我我就信？给证据！”',[-1,1,2,2,-1]],
['嘴上说不信，心里还保留一点偏爱。',[1,-1,-1,1,2]],
['“游戏结束之后，我们能不能也聊聊？”',[2,0,2,1,1]]]},
{scene:'10 / 后会友期：最后一站',fact:'节目核心命题：重逢之后可以继续同行，也可以体面告别，不强制和好。',title:'车要到站了，旧友问你：“我们以后还会见面吗？”你最想回答？',opts:[
['“有机会的。下次，我主动约。”',[2,-1,2,2,1]],
['“不知道，但能把这段旅程走完已经很好了。”',[-1,1,0,-1,-1]],
['“先把没说完的话说清楚，再谈以后。”',[1,0,2,1,0]],
['“我会记得你，也会继续走自己的路。”',[-2,2,-1,-1,0]]]}
];
const app=document.getElementById('app');
let answers=Array(Q.length).fill(-1),step=0,current=null,selectedTemplate='cinema',customPhotos={},imgCache={};
const $=s=>document.querySelector(s);
const e=s=>String(s).replace(/[&<>"']/g,k=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[k]));
function toast(s){const t=$('#toast');if(!t)return;t.textContent=s;t.classList.add('on');clearTimeout(toast.timer);toast.timer=setTimeout(()=>t.classList.remove('on'),3000)}
function nav(dark=false){return '<div class="v2-nav '+(dark?'dark':'')+'"><a href="'+APP_PATH+'" class="v2-brand">HOU HUI YOU QI / 后会友期</a><span class="v2-mini">非官方粉丝创作 · V2</span></div>'}
function reset(){step=0;answers=Array(Q.length).fill(-1);sessionStorage.removeItem('hhyq-progress');history.replaceState({},'',location.pathname);renderQuestion()}
function saveProgress(){try{sessionStorage.setItem('hhyq-progress',JSON.stringify({answers,step}))}catch{}}
function resume(){try{const s=JSON.parse(sessionStorage.getItem('hhyq-progress'));if(s&&Array.isArray(s.answers)&&s.answers.length===Q.length&&s.answers.every(a=>a>=-1&&a<4)){answers=s.answers;step=Math.max(0,Math.min(Q.length-1,s.step||0));return true}}catch{}return false}
function home(){document.title='谁是你的友情嘴替｜后会友期非官方趣味测试';window.scrollTo(0,0);
app.innerHTML='<main class="v2-home">'+nav()+'<div class="v2-hero"><section><div class="v2-kicker">FRIENDSHIP / 友情售后中心</div><h1>旧友重逢，<br><em>谁是你的</em><br>互联网嘴替？</h1><p>删了微信，马克杯还记得；想和好，嘴比心硬；关系越界了，先启动门禁。<br>10个《后会友期》名场面衍生选择题，测测你更像哪种友情人设。</p><div class="v2-badges"><span>10题 / 约2分钟</span><span>8位嘉宾友情原型</span><span>4款可选分享海报</span></div><button class="v2-btn" id="start">🚂 上车，测我的友情人设 →</button> '+(sessionStorage.getItem('hhyq-progress')?'<button class="v2-btn outline" id="continue" style="color:#f9e9d4;border-color:#ffffff66;margin-left:8px">继续上次答题</button>':'')+'<div class="v2-hint">本人设为节目情境二创，不是嘉宾本人心理评估；可自己选择和上传有权使用的照片。</div></section><div class="v2-hero-visual"><div class="v2-hero-art"><div class="v2-hero-stamp">十年没联系，<br>这次你先开口吗？<small>THE NEXT STOP IS AN ANSWER</small></div></div></div></div></main>';
$('#start').onclick=reset;const c=$('#continue');if(c)c.onclick=()=>{resume();renderQuestion()};
}
function renderQuestion(){document.title='第'+(step+1)+'站｜后会友期友情人格测试';window.scrollTo(0,0);let q=Q[step];
app.innerHTML='<main class="v2-shell">'+nav(true)+'<div class="v2-body"><div class="v2-prog-head"><span>友情售后工单 · 第'+(step+1)+'站</span><span>'+(step+1)+' / '+Q.length+'</span></div><div class="v2-progress"><div style="width:'+Math.round(step/Q.length*100)+'%"></div></div><div class="v2-episode">'+e(q.scene)+'</div><section class="v2-question"><h2>'+e(q.title)+'</h2><p class="notice">'+e(q.fact)+'<br><small>以下为原创情境选项，不是嘉宾在节目中的真实作答。</small></p>'+q.opts.map((o,i)=>'<button data-ans="'+i+'" class="v2-choice '+(answers[step]===i?'active':'')+'"><b>'+('ABCD'[i])+'</b><span>'+e(o[0])+'</span></button>').join('')+'</section><div class="v2-qfoot"><button class="v2-textbtn" id="back">'+(step?'← 上一站':'← 回首页')+'</button><button class="v2-btn dark" id="forward" '+(answers[step]<0?'disabled':'')+'>'+(step===Q.length-1?'揭晓我的互联网嘴替 →':'下一站 →')+'</button></div><div class="v2-deco">没有标准答案，第一反应最像你的友情相处方式。</div></div></main>';
document.querySelectorAll('[data-ans]').forEach(b=>b.onclick=()=>{answers[step]=Number(b.dataset.ans);saveProgress();renderChoice()});
$('#back').onclick=()=>{if(step===0)home();else{step--;saveProgress();renderQuestion()}};
$('#forward').onclick=()=>{if(answers[step]<0)return;if(step===Q.length-1){current=scoreResult();sessionStorage.removeItem('hhyq-progress');history.replaceState({},'',location.pathname+'?r='+current.id);renderResult()}else{step++;saveProgress();renderQuestion()}};
}
function renderChoice(){document.querySelectorAll('[data-ans]').forEach(b=>b.classList.toggle('active',Number(b.dataset.ans)===answers[step]));$('#forward').disabled=false}
const choiceAnchors = {"li":[2,1,2,2,2,2,1,1,0,3],"xu":[3,3,3,3,1,0,0,2,3,2],"zhang":[0,0,0,0,0,0,3,3,3,0],"ma":[1,1,1,2,2,1,1,1,0,1],"wen":[1,2,3,1,1,3,0,0,2,0],"wang":[2,0,1,2,3,1,1,1,0,3],"qing":[0,0,3,0,0,0,3,3,2,0],"bai":[3,3,1,3,3,1,1,2,1,2]};
function scoreResult(){
const v=scoreForTests(answers);
const ranking=characters.map((c,i)=>{
const dimensions=c.dims.reduce((sum,x,k)=>sum+(x-v[k])**2*(k===4?1.12:1),0)/50000;
const choices=answers.reduce((sum,a,k)=>sum+(a!==choiceAnchors[c.id][k]),0)/Q.length;
return {c,dist:.4*choices+.6*dimensions+i*0.0000001};
}).sort((a,b)=>a.dist-b.dist);
ranking[0].c.runner=ranking[1].c.name;return ranking[0].c;
}
function getPhotoSrc(id){return customPhotos[id]||(photoSources[id]&&photoSources[id].url)||''}
function picture(id){const src=getPhotoSrc(id);if(!src)return '';
return '<img data-character-photo="'+id+'" src="'+e(src)+'" crossorigin="anonymous" alt="'+e(C[id].name)+'人物照片" onerror="this.style.display=\'none\';this.parentElement.classList.add(\'photo-unavailable\');" />'}
function characterCard(c){let has=getPhotoSrc(c.id);
return '<section class="v2-character"><div class="v2-photo"><div class="fallback-art"><span class="word">'+e(c.name)+'</span><span class="sub">你的友情类型 / '+(has?'照片加载失败可自行更换':'请上传有权使用的角色照片')+'</span></div>'+picture(c.id)+'<span class="v2-portrait-tag">'+(has?'人物照片 / 可更换':'人物姓名艺术卡 / 待添加照片')+'</span></div><div class="v2-character-copy"><div class="smallcaps">YOUR FRIENDSHIP TYPE</div><h2>'+e(c.title)+'</h2><div class="quot">'+e(c.stamp)+'</div><div class="v2-hashtags">'+c.tags.map(t=>'<span>#'+e(t)+'</span>').join('')+'</div></div></section>'}
function resultDetails(c){return '<section class="v2-analysis"><div class="v2-section-label">01 / 你的互联网弹幕</div><div class="v2-bubble">'+e(c.meme).replace(/\n/g,'<br>')+'</div><div class="v2-section-label">02 / 表面和内心两套系统</div><p class="v2-p">'+e(c.caption).replace(/\n/g,'<br>')+'</p><div class="v2-section-label">03 / 说点真正戳心的</div><p class="v2-p">'+e(c.touch)+'</p><div class="v2-section-label">04 / 友情翻车预警</div><p class="v2-p">'+e(c.weak)+'</p><div class="v2-section-label">05 / 下一站小纸条</div><div class="v2-soul">'+e(c.mission)+'</div><div class="v2-scene"><b>节目对应情境：</b>'+e(c.scenetitle.replace('节目对应：',''))+'<br><a href="'+e(c.scenesrc)+'" target="_blank" rel="noopener noreferrer">查看芒果TV节目资料 ↗</a><br><small>人物标签与梗文案均为原创趣味类比，并非嘉宾真实发言或科学测评。</small></div><div class="v2-actions"><button class="v2-btn dark" id="go-poster">选我的海报 ↓</button><button class="v2-btn outline" id="share-link">↗ 分享结果</button><button class="v2-btn outline" id="restart">↺ 再测一次</button></div><p class="v2-cta-note">节目里不一定每段友情都要和好。你也不用把自己活成哪位嘉宾，这是一次好玩的关系投射。</p></section>'}
function resultHTML(c){return '<main class="v2-shell">'+nav(true)+'<header class="v2-result-head"><div class="eyebrow">RESULT / 友情嘴替鉴定书</div><h1>你测出了 <span style="color:#ad7b4c">'+e(c.name)+'</span> 型</h1><p>你不是被“判定”为某位真人，只是在某种友情处境下，与你选中的节目人物原型相似。</p></header><div class="v2-result-grid">'+characterCard(c)+resultDetails(c)+'</div><section class="v2-panel" id="poster-chooser"><h2>来，选一张你愿意发朋友圈的海报</h2><p>四种排版不是换色皮肤。点击就能预览并选用。下方可以切换人物检查每张卡片是否好看。</p><div class="v2-templates">'+templates.map(t=>'<button class="v2-template '+(t.id===selectedTemplate?'active':'')+'" data-template="'+t.id+'"><canvas id="canvas-'+t.id+'" width="270" height="480" aria-label="'+e(t.name)+'预览"></canvas><strong>'+e(t.name)+'</strong><small>'+e(t.desc)+'</small></button>').join('')+'</div><div class="v2-design-toolbar"><select id="character-preview" class="v2-select" aria-label="预览其他角色">'+characters.map(p=>'<option value="'+p.id+'" '+(p.id===c.id?'selected':'')+'>'+e(p.name)+'</option>').join('')+'</select><button class="v2-btn dark" id="download">保存当前海报 PNG ↓</button><button class="v2-btn outline" id="upload-button">上传/替换人物照片</button><button class="v2-btn outline" id="copy-caption">复制朋友圈文案</button></div><div class="v2-banner"><b>关于照片：</b>只有部分人物有可核实来源的公开许可图片。其他人物不再显示灰色人形冒充真图——请使用「上传/替换人物照片」选择你有权使用的照片，预览与导出同步更新。你上传的图片仅留在当前浏览器，不会上传到服务器；分享链接不会携带你的图片。</div></section><footer class="v2-footer">《后会友期》非官方粉丝互动作品。题目参考芒果TV公开节目情境，结果是原创设定，不代表真人真实人格。<br>节目资料：<a href="'+EVIDENCE+'" target="_blank" rel="noopener noreferrer">芒果TV官方节目页</a>。<span id="image-credit"></span></footer><input hidden id="photo-upload" type="file" accept="image/jpeg,image/png,image/webp"></main>'}
function renderResult(){if(!current)return home();window.scrollTo(0,0);document.title='我是'+current.name+'型友情人格｜后会友期人物测试';app.innerHTML=resultHTML(current);
$('#restart').onclick=reset;$('#share-link').onclick=share;$('#go-poster').onclick=()=>document.getElementById('poster-chooser').scrollIntoView({behavior:'smooth'});
$('#download').onclick=download;$('#copy-caption').onclick=copyCaption;
document.querySelectorAll('[data-template]').forEach(x=>x.onclick=()=>{selectedTemplate=x.dataset.template;localStorage.setItem('hhyq-template',selectedTemplate);document.querySelectorAll('[data-template]').forEach(y=>y.classList.toggle('active',x===y));toast('已选中'+templates.find(t=>t.id===selectedTemplate).name)});
$('#character-preview').onchange=x=>{current=C[x.target.value];history.replaceState({},'',location.pathname+'?r='+current.id);renderResult()};
$('#upload-button').onclick=()=>$('#photo-upload').click();
$('#photo-upload').onchange=handleUpload;
const credit=photoSources[current.id];if(credit&&!customPhotos[current.id]){$('#image-credit').innerHTML='<br>照片资料来源：<a href="'+e(credit.source)+'" target="_blank" rel="noopener noreferrer">'+e(credit.credit)+'</a>；<a href="https://creativecommons.org/licenses/by/2.5/" target="_blank" rel="noopener noreferrer">图片许可 CC BY 2.5</a>。'}
renderAllPreviews();
}
function scoreForTests(a){const totals=[0,0,0,0,0];a.forEach((pick,i)=>Q[i].opts[pick][1].forEach((v,j)=>totals[j]+=v));return totals.map(t=>Math.max(0,Math.min(100,50+t*2.5)))}
function fallbackCopy(text){let ta=document.createElement('textarea');ta.value=text;ta.style.position='absolute';ta.style.left='-9999px';document.body.appendChild(ta);ta.select();document.execCommand('copy');ta.remove()}
async function copyText(text){try{await navigator.clipboard.writeText(text)}catch{fallbackCopy(text)}}
function copyCaption(){copyText('我测出了《后会友期》里的「'+current.name+'」型友情人设——'+current.title+'。\n'+current.stamp+'\n不是我对号入座，是这档节目在我心里装监控了。\n你测出谁？ '+APP_PATH).then(()=>toast('朋友圈文案已复制'))}
async function share(){const text='我测出了《后会友期》友情人设：'+current.title+'。你也来测测！';const url=APP_PATH+'?r='+current.id;try{if(navigator.share)await navigator.share({title:'谁是你的友情嘴替？',text,url});else{await copyText(text+'\n'+url);toast('结果链接已复制')}}catch(err){if(err.name!=='AbortError'){await copyText(text+'\n'+url);toast('结果链接已复制')}}}
function dbOpen(){return new Promise((resolve,reject)=>{if(!window.indexedDB)return reject(Error('No DB'));const r=indexedDB.open('hhyq-photos',1);r.onupgradeneeded=()=>r.result.createObjectStore('pictures');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
async function savePhoto(id,s){try{const db=await dbOpen();await new Promise((resolve,reject)=>{const t=db.transaction('pictures','readwrite');t.objectStore('pictures').put(s,id);t.oncomplete=resolve;t.onerror=()=>reject(t.error)});db.close()}catch{toast('图片已用于当前页面，但浏览器未允许本地保存')}}
async function restorePhotos(){try{const db=await dbOpen();const values=await Promise.all(characters.map(p=>new Promise(res=>{const t=db.transaction('pictures');const req=t.objectStore('pictures').get(p.id);req.onsuccess=()=>res([p.id,req.result]);req.onerror=()=>res([p.id,null])})));for(const [id,uri] of values)if(uri)customPhotos[id]=uri;db.close()}catch{}}
function compressFile(file){return new Promise((resolve,reject)=>{const fr=new FileReader();fr.onerror=()=>reject(Error('read'));fr.onload=()=>{const im=new Image();im.onerror=()=>reject(Error('image'));im.onload=()=>{const r=Math.min(1,1350/Math.max(im.width,im.height));const cv=document.createElement('canvas');cv.width=Math.max(1,Math.round(im.width*r));cv.height=Math.max(1,Math.round(im.height*r));const ctx=cv.getContext('2d');ctx.drawImage(im,0,0,cv.width,cv.height);resolve(cv.toDataURL('image/jpeg',.88))};im.src=fr.result};fr.readAsDataURL(file)})}
async function handleUpload(ev){const file=ev.target.files&&ev.target.files[0];if(!file)return;if(!file.type.startsWith('image/'))return toast('请选择照片文件');if(file.size>18*1024*1024)return toast('请使用小于18MB的图片');try{const uri=await compressFile(file);customPhotos[current.id]=uri;delete imgCache[current.id];await savePhoto(current.id,uri);renderResult();toast('照片已更新，并用于所有海报！')}catch{toast('照片读取失败，请换张图片')}}
function photoImg(id){const src=getPhotoSrc(id);if(!src)return Promise.resolve(null);if(imgCache[id]&&imgCache[id].src===src)return imgCache[id].promise;const promise=new Promise(resolve=>{const im=new Image();if(!src.startsWith('data:'))im.crossOrigin='anonymous';let called=false;const finish=a=>{if(called)return;called=true;clearTimeout(timer);resolve(a)};im.onload=()=>finish(im);im.onerror=()=>finish(null);const timer=setTimeout(()=>finish(null),7000);im.src=src});imgCache[id]={src,promise};return promise}
function rounded(ctx,x,y,w,h,r,fill){ctx.fillStyle=fill;ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fill()}
function fillImage(ctx,img,x,y,w,h){if(!img)return false;try{const sc=Math.max(w/img.naturalWidth,h/img.naturalHeight),sw=img.naturalWidth*sc,sh=img.naturalHeight*sc;ctx.drawImage(img,x+(w-sw)/2,y+(h-sh)/2,sw,sh);return true}catch{return false}}
function textWrap(ctx,text,x,y,width,lineHeight,limit){let line='',row=0;for(const char of text){if(char==='\n'){ctx.fillText(line,x,y+row*lineHeight);row++;line='';continue}if(ctx.measureText(line+char).width>width&&line){ctx.fillText(line,x,y+row*lineHeight);row++;line='';if(row>=limit)return}line+=char}if(line&&row<limit)ctx.fillText(line,x,y+row*lineHeight)}
function textPos(ctx,t,x,y,size,color,bold=false){ctx.fillStyle=color;ctx.font=(bold?'700 ':'400 ')+size+'px "Noto Sans SC","PingFang SC",sans-serif';ctx.fillText(t,x,y)}
function fallbackCanvas(ctx,x,y,w,h,c){const grad=ctx.createLinearGradient(x,y,x+w,y+h);grad.addColorStop(0,'#879d9a');grad.addColorStop(.55,c.theme);grad.addColorStop(1,'#183648');ctx.fillStyle=grad;ctx.fillRect(x,y,w,h);ctx.fillStyle='#efc58f';ctx.globalAlpha=.65;ctx.beginPath();ctx.arc(x+w*.76,y+h*.26,Math.min(w,h)*.13,0,Math.PI*2);ctx.fill();ctx.globalAlpha=1;
ctx.fillStyle='#1c3542';ctx.beginPath();ctx.moveTo(x,y+h*.68);ctx.lineTo(x+w*.37,y+h*.39);ctx.lineTo(x+w*.57,y+h*.61);ctx.lineTo(x+w*.81,y+h*.36);ctx.lineTo(x+w,y+h*.6);ctx.lineTo(x+w,y+h);ctx.lineTo(x,y+h);ctx.fill();
ctx.fillStyle='#fff3dd';ctx.font='92px "Songti SC",serif';ctx.fillText(c.name,x+45,y+h*.82);textPos(ctx,'上传人物照片即可替换这张艺术卡',x+43,y+h*.91,18,'#efdbba')}
function putPhoto(ctx,img,x,y,w,h,c){ctx.save();ctx.beginPath();ctx.rect(x,y,w,h);ctx.clip();if(!fillImage(ctx,img,x,y,w,h))fallbackCanvas(ctx,x,y,w,h,c);ctx.restore()}
function gradient(ctx,c1,c2){let g=ctx.createLinearGradient(0,0,900,1600);g.addColorStop(0,c1);g.addColorStop(1,c2);ctx.fillStyle=g;ctx.fillRect(0,0,900,1600)}
function drawCanvas(cvs,c,img,t){
const ctx=cvs.getContext('2d');const W=900,H=1600;ctx.setTransform(cvs.width/W,0,0,cvs.height/H,0,0);ctx.clearRect(0,0,W,H);const name=c.name,one=c.stamp;
if(t==='cinema'){gradient(ctx,'#1a3546','#987961');ctx.fillStyle='#f3c997';ctx.beginPath();ctx.arc(690,235,170,0,7);ctx.fill();ctx.fillStyle='#1d3544';ctx.beginPath();ctx.moveTo(0,1050);ctx.lineTo(290,750);ctx.lineTo(500,1000);ctx.lineTo(740,710);ctx.lineTo(900,940);ctx.lineTo(900,1600);ctx.lineTo(0,1600);ctx.fill();
textPos(ctx,'HOU HUI YOU QI  /  FRIENDSHIP',60,80,23,'#fce6c8',true);textPos(ctx,'旧友重逢，谁是你的互联网嘴替？',60,133,21,'#f2d7ae');
ctx.save();ctx.shadowColor='#102330';ctx.shadowBlur=36;rounded(ctx,76,196,748,956,16,'#f0e7d8');ctx.restore();putPhoto(ctx,img,104,222,692,704,c);
ctx.fillStyle='#274558';ctx.font='76px "Songti SC",serif';ctx.fillText(name,130,1012);
textPos(ctx,c.title,130,1060,26,'#304a58');ctx.fillStyle='#d4ab73';ctx.fillRect(82,1190,75,5);
ctx.fillStyle='#f8e6ca';ctx.font='37px "Songti SC",serif';textWrap(ctx,one,88,1271,760,58,3);
textPos(ctx,'#后会友期  #友情嘴替',85,1490,20,'#f8d4aa');textPos(ctx,'非官方趣味测试 · 不是嘉宾真实人格评估',85,1540,17,'#dae2e0');
}
else if(t==='ticket'){gradient(ctx,'#e8e0cb','#a99374');rounded(ctx,47,57,806,1484,27,'#fff9ea');ctx.strokeStyle='#ad9172';ctx.setLineDash([13,10]);ctx.lineWidth=3;ctx.strokeRect(67,78,764,1440);ctx.setLineDash([]);textPos(ctx,'FRIENDSHIP EXPRESS / 友情车票',95,140,26,'#334f60',true);textPos(ctx,'DESTINATION: THE NEXT CHAPTER',95,188,19,'#aa855c');putPhoto(ctx,img,96,235,708,715,c);
textPos(ctx,'旅客姓名 / CHARACTER',95,1031,22,'#997c5d');ctx.fillStyle='#243c48';ctx.font='92px "Songti SC",serif';ctx.fillText(name,95,1136);
ctx.fillStyle='#d2ba94';ctx.fillRect(96,1164,703,3);
ctx.font='30px "Noto Sans SC",sans-serif';ctx.fillStyle='#334c55';textWrap(ctx,c.title,95,1218,660,47,2);ctx.font='25px "Noto Sans SC",sans-serif';textWrap(ctx,one,95,1350,700,46,2);
textPos(ctx,'票据仅供游戏收藏 · 不代表实际车次',96,1466,18,'#967e60');
}
else if(t==='magazine'){gradient(ctx,'#f8f1e4','#e5d8c7');rounded(ctx,41,51,818,1500,10,'#faf8f1');putPhoto(ctx,img,62,125,776,1030,c);
ctx.fillStyle='rgba(14,31,44,.54)';ctx.fillRect(62,800,776,355);
ctx.fillStyle='#fff';ctx.font='100px "Songti SC",serif';ctx.fillText(name,98,1043);
textPos(ctx,'THE FRIENDSHIP ISSUE   /   2026',72,93,22,'#203d4a',true);
textPos(ctx,'你的友情角色特刊',84,1200,23,'#bd895d');
ctx.fillStyle='#233c47';ctx.font='35px "Noto Sans SC",sans-serif';textWrap(ctx,c.title,84,1273,715,50,2);
ctx.font='31px "Songti SC",serif';textWrap(ctx,one,84,1413,740,50,2);
textPos(ctx,'非官方角色类比 · 分享你的朋友圈封面',84,1525,17,'#6b7880');
}
else {gradient(ctx,'#ecb6a2','#f1d5b4');ctx.fillStyle='#364e59';ctx.fillRect(38,39,824,1522);
textPos(ctx,'# 后会友期友谊弹幕区',85,119,29,'#f6d5aa',true);rounded(ctx,82,165,736,811,36,'#f6f2e9');putPhoto(ctx,img,107,191,686,760,c);rounded(ctx,85,1005,725,103,20,'#f6d1a0');
ctx.fillStyle='#233d4d';ctx.font='37px "Songti SC",serif';textWrap(ctx,c.title,116,1064,660,52,2);
rounded(ctx,82,1160,736,235,26,'#fbf6ef');ctx.fillStyle='#283e48';ctx.font='26px "Noto Sans SC",sans-serif';textWrap(ctx,c.meme,120,1220,650,42,4);
textPos(ctx,'很像我 · 但是这个结果我先发给朋友',91,1475,19,'#f5dbad');
textPos(ctx,'非官方趣味游戏 / 不是嘉宾真实发言',91,1530,15,'#bdc6c1');
}
if(img&&photoSources[c.id]&&!customPhotos[c.id]){textPos(ctx,'PHOTO: RAYOFSUNSHINE / CC BY 2.5',90,t==='ticket'?1510:(t==='magazine'?1550:1580),15,(t==='ticket'||t==='magazine')?'#65727a':'#f7e5d3')}
}
async function renderAllPreviews(){if(!current)return;const id=current.id;const im=await photoImg(id);if(!current||current.id!==id)return;for(const t of templates){let cvs=document.getElementById('canvas-'+t.id);if(cvs)drawCanvas(cvs,current,im,t.id)}}
async function download(){if(!current)return;let b=$('#download');b.disabled=true;b.textContent='正在生成海报…';try{let cvs=document.createElement('canvas');cvs.width=1080;cvs.height=1920;const im=await photoImg(current.id);drawCanvas(cvs,current,im,selectedTemplate);await new Promise((resolve,reject)=>cvs.toBlob(blob=>{if(!blob)return reject(Error('canvas'));const url=URL.createObjectURL(blob);let a=document.createElement('a');a.href=url;a.download='后会友期-友情嘴替-'+current.name+'-'+selectedTemplate+'.png';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),8000);resolve()},'image/png'));toast(im?'海报已保存，带上照片发朋友圈吧！':'海报已保存，若要真人照片可上传后重新导出')}
catch(err){toast('图片生成失败，可先截图或更换照片再试')}finally{b.disabled=false;b.textContent='保存当前海报 PNG ↓'}}
async function init(){try{const t=localStorage.getItem('hhyq-template');if(templates.some(x=>x.id===t))selectedTemplate=t}catch{}
await restorePhotos();const r=new URL(location.href).searchParams.get('r');if(r&&C[r]){current=C[r];renderResult()}else home()}
window.addEventListener('popstate',()=>{const r=new URL(location.href).searchParams.get('r');if(r&&C[r]){current=C[r];renderResult()}else home()});
init();
