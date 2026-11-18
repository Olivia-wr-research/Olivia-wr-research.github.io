'use strict';
/* 《后会友期》友情人物测试 v3
   非官方粉丝创作：情境来自公开节目片段，人物标签与文案为原创趣味类比。 */

const APP_PATH = 'https://olivia-wr-research.github.io/apps/houhuiyouqi-quiz/';
const EPISODE = 'https://www.mgtv.com/h/914227.html';
const EVIDENCE = 'https://www.mgtv.com/act/2026/hhyq2026/';

const templates = [
  { id: 'cinema',  name: 'A / 公路电影', desc: '一张电影帧' },
  { id: 'ticket',  name: 'B / 友情车票', desc: '一张不退票' },
  { id: 'magazine',name: 'C / 人物特刊', desc: '一期封面' },
  { id: 'thread',  name: 'D / 评论区',   desc: '一条弹幕' }
];

const photoSources = Object.fromEntries(
  ['li','xu','zhang','ma','wen','wang','qing','bai'].map(id => [
    id, { url: './photos/' + id + '.webp', credit: '人物照片由站点维护者提供；据其说明来自官方平台发布，版权归原权利人。' }
  ])
);

const characters = [
{id:'li',nick:'画地为牢本人',name:'厉娜',title:'友情「已读但不强制原谅」派',stamp:'不和好也可以是结局',meme:'别人：都这么久了，你还不翻篇？\n你：日历会自动翻页，关系又不是自动续费。',caption:'表面：没什么好说的。\n心里：发生过的事，不会因为时间久就变成没发生。',touch:'你不是把旧事记成账本，而是知道有些伤口不能靠一句“算了吧”解决。你可以允许对方把话说完，也允许自己保留感受。对你来说，体面的告别和重新开始一样值得尊重。',weak:'太习惯自己消化情绪，别人可能不知道你真的有多难过。',mission:'你的友情通关提示：不必为了证明大度，把还没愈合的事轻轻带过。',scenetitle:'节目对应：厉娜与许飞车上对谈，以及“不一定继续做朋友”的表达',scenesrc:EVIDENCE,pair:'许飞',tags:['边界先于和解','慢热但记得','可以体面告别'],dims:[24,80,29,34,40],hots:[['「我画地为牢啊，厉娜」——被全网改成填空题：我画地为牢啊，早八；我画地为牢啊，甲方。','出圈梗 · 抖音同名话题 40 亿播放'],['她的原话是“不一定继续做朋友”。节目播出后这句被做成了表情包。','节目立场 · 二创表情包']],duo:'你画地为牢，TA 把这段关系当成句号。烧烤时他还是会把烟扇到另一边，但那不等于他要回头。',theme:'#748b95'},
{id:'xu',nick:'老兵烧烤',name:'许飞',title:'友情「往事售后客服」派',stamp:'工单可以关闭，话要说完',meme:'别人：都过去十几年了。\n你：时间是过去了，我的未读消息还没处理。',caption:'嘴上：都过去了。\n脑内：那段友情的复盘文档已自动打开第18版。',touch:'你在意的不是赢一场争论，而是想知道两个人为什么从亲近走到了这里。你愿意翻开旧信，也愿意试着把没说完的话讲出来。但你慢慢会明白：表达你的版本很重要，接受对方未必给你同一种答案也很重要。',weak:'你有时候把“说清楚”误当成“还能回到从前”。',mission:'你的友情通关提示：说完想说的话，就已经完成了自己的那一部分。',scenetitle:'节目对应：许飞读介绍信落泪、与厉娜谈过往及询问能否重新做朋友',scenesrc:EVIDENCE,pair:'厉娜',tags:['未完待续型','复盘十级学者','情感存档'],dims:[83,38,62,50,58],hots:[['「老兵烧烤」：烧烤环节看见厉娜走近，他下意识把扇子调转方向，不让油烟飘过去。','出圈外号 · 本人后来穿迷彩“出摊”'],['2011 年特招入伍，在部队创作室待了近八年，平时也自称“老兵”。','背景 · “老兵”是这么来的'],['「我等这一刻等了十五年了」被剪成 BGM，配毕业、送别、旧友重逢的视频。','二创热句']],duo:'你把烟扇到另一边，也把话说完。TA 把话收好，也把门关上。',theme:'#7b9b91'},
{id:'zhang',nick:'马克杯守墓人',name:'张萌',title:'友情「删了微信也要送杯子」派',stamp:'朋友可以断联，礼物不能缺席',meme:'别人：都断联了还买礼物？\n你：好友可以不在列表，但还在我的购物灵感里。',caption:'嘴上：没关系，不联系就算了。\n购物车：这杯子TA应该会喜欢。',touch:'你是那种看到一个小物件就会突然想到某个旧友的人。对你来说，关系不是一道非黑即白的选择题。你愿意主动靠近，也容易在热情里忘记：对方或许还没有准备好。你的勇敢很珍贵，尊重对方的节奏也很重要。',weak:'好意跑得比沟通快，偶尔会变成别人感受到的压力。',mission:'你的友情通关提示：送礼物之前，先确认对方愿不愿意重新打开那扇门。',scenetitle:'节目对应：张萌提到断联期间仍记得马天宇喜欢收藏马克杯',scenesrc:EPISODE,pair:'马天宇',tags:['纪念型人格','礼物派','热情先行'],dims:[88,45,30,66,44],hots:[['“你还记得你喜欢收藏马克杯吗”——那条视频在抖音拿到 89 万赞，评论区集体破防。','抖音高赞名场面'],['断联十年，礼物照买，只是好友列表里已经没有这个人了。','名场面 · 十年']],duo:'你记得那只马克杯，TA 记得被越界的那一次。同一年，两种记法。',theme:'#a8825f'},
{id:'ma',nick:'郊区返乡人',name:'马天宇',title:'友情「边界感保安队长」派',stamp:'请先刷卡，再进我的舒适区',meme:'别人：我们关系这么好，你还分什么边界？\n你：好朋友也得敲门，门禁不是装饰。',caption:'表面：我只想自己待会儿。\n真心：我很珍惜你，但我不能把所有空间都交出去。',touch:'你喜欢的是彼此尊重、允许各自独处的关系。对方太急于替你安排时，你会迅速感到疲惫。你不一定少情，也不一定冷淡；你只是更相信，长久的亲密应该留得下自由活动的空间。',weak:'你习惯用退后表示不舒服，别人可能根本没有收到通知。',mission:'你的友情通关提示：边界明确很酷，偶尔解释清楚会更省力。',scenetitle:'节目对应：马天宇谈享受独处，并就张萌的相处方式表达边界感',scenesrc:EVIDENCE,pair:'张萌',tags:['独处是刚需','越界提醒器','尊重双向选择'],dims:[26,86,40,20,62],hots:[['「人类好可怕，我要回郊区了」——密友数测出零之后，这句话成了社恐的官方签名。','节目名场面'],['心结卡环节，他把白小纯写的那句“训练像坐牢”当众念了出来。','名场面 · 大声念']],duo:'你要边界，TA 要靠近。你在心结卡环节替人念了心事，念得很大声。',theme:'#66808f'},
{id:'wen',nick:'友情仅退款',name:'文吉儿',title:'友情「唯一好友单推人」派',stamp:'我不是要绑住你，只想确定我很重要',meme:'别人：朋友又不是单选题。\n你：我知道啊，我只是想当那道压轴大题。',caption:'嘴上：你交新朋友没关系。\n心里：那我们的专属默契，还有没有名字？',touch:'你能接受朋友拥有自己的世界，却很在意某种只有彼此才懂的连接是否还存在。你会记住过去的承诺，也会敏锐地察觉关系的微小变化。你想要的并不是控制，而是一份被认真放在心上的确定感。',weak:'当亲密的定义不一样时，你可能把对方的自由误读成自己不够重要。',mission:'你的友情通关提示：与其猜自己是不是唯一，不如说出你真正想被怎样对待。',scenetitle:'节目对应：文吉儿与王子璇对好友“唯一性”的期待差异',scenesrc:EPISODE,pair:'王子璇',tags:['专属感','记得承诺','需要确定'],dims:[62,42,88,30,46],hots:[['三万块写序费的旧账，被网友换算成电商术语：「友情仅退款」。','微博 / 小红书热评'],['她保存了八年的转账记录和聊天截图，在节目里当众摊开。','名场面 · 八年证据']],duo:'你要唯一，TA 要自由。争到最后，落在一张八年前的账单上。',theme:'#a0726f'},
{id:'wang',nick:'不做朋友了',name:'王子璇',title:'友情「好友列表非单选」派',stamp:'亲密不是独占，真诚才是必选',meme:'别人：我是你唯一的朋友吗？\n你：你是重要的人，但我的通讯录不参加排他赛。',caption:'表面：大家都能好好相处。\n心里：为什么我交新朋友，也需要交一份解释报告？',touch:'你珍惜亲密，也看重相处中的选择空间。对你来说，友谊不是占有权证明，而是各自都能自然做自己。可当对方特别需要确定感时，你的轻松可能被听成疏远；你也需要学会把“重要”说得更具体。',weak:'过分相信“对方应该懂”，往往让沉默变成了误解。',mission:'你的友情通关提示：自由是底色，让对方感到被珍惜也并不矛盾。',scenetitle:'节目对应：王子璇与文吉儿围绕朋友关系及亲密期待的讨论',scenesrc:EPISODE,pair:'文吉儿',tags:['不排他','自在优先','直给沟通'],dims:[58,30,22,82,34],hots:[['「我不想做朋友了」——评论区统一盖章：成年人最体面的绝交，是一句不解释的结束。','节目名场面'],['游戏环节她逗青稚“有点凡尔赛”，转头又夸白小纯是队里的大哥。','名场面 · 凡尔赛']],duo:'你要自在，TA 要确定。你说不想做朋友了，TA 说先把话说完。',theme:'#7d9a86'},
{id:'qing',nick:'雷王',name:'青稚',title:'友情「前队友复活赛」派',stamp:'你先别退队，我们再打一次',meme:'别人：都不是队友了，还惦记呢？\n你：战队能换，老搭档的默契哪有一键卸载。',caption:'嘴上：大家各走各的路。\n身体：对方有事，我先冲过去。',touch:'你很重视并肩作战积累出来的默契，所以当合作变了味，你往往比别人更难受。你可能嘴硬、可能急着争个结果，但心里其实还希望彼此能再次好好配合。有些关系不是不重要，而是你们还没学会用同一种速度沟通。',weak:'你太想立刻推进局面，反而可能让需要冷静的人更想后退。',mission:'你的友情通关提示：想重组一支队伍，第一步也许不是冲锋，而是听清对方想去哪。',scenetitle:'节目对应：青稚白小纯领队意见不合、旅行中落泪与尝试重新同行',scenesrc:EVIDENCE,pair:'白小纯',tags:['战友型','不想散场','行动先行'],dims:[80,26,66,72,30],hots:[['奖杯柜里有一座「雷神杯」，网友直接封他雷王；还有那句「不过是山下的人，怎么嘲笑山上的神」。','电竞二创 · 雷王出处'],['「土皇帝」这个老外号被考古出来，源头是他对训练近乎苛刻的要求。','梗 · 土皇帝'],['2026 PMMI FMVP、2024 PEL 春季赛总决赛 FMVP，本名张庆波，21 岁。','背景 · 荣誉墙']],duo:'一本摊开的书，遇上不看字的人。先对账，再搬行李，谁都没先低头。',theme:'#6f8894'},
{id:'bai',nick:'一本摊开的书',name:'白小纯',title:'友情「先对线后搬行李」派',stamp:'道理要讲，忙也能帮',meme:'别人：你俩不是吵架了吗？\n你：吵归吵，行李那么重，手也不能闲着啊。',caption:'表面：这件事我有我的观点。\n真心：但我也没说不在乎你。',touch:'你不是遇事会轻易低头的人，讲道理、保留立场对你很重要。可这不妨碍你在具体的事上伸手帮忙。你知道关系的复杂就在这里：情绪可以拧巴，行动里却仍然留着温度。',weak:'当你太在意把事情讲对，别人可能只听到了你的态度，没有看到你的关心。',mission:'你的友情通关提示：观点可以先放桌上，心意也值得被对方看见。',scenetitle:'节目对应：白小纯与青稚争执后仍帮忙搬行李、邀请回屋',scenesrc:EVIDENCE,pair:'青稚',tags:['行动派嘴替','不服软但会帮忙','理性在线'],dims:[40,52,58,86,42],hots:[['「白小纯是一本摊开的书，可惜青稚不识字。」','抖音热梗 · 纯稚'],['网友补刀：马天宇不仅识字，还大声念给青稚听——心结卡那句“训练像坐牢”，他本以为只写给自己看。','热评 · 代读梗'],['「明明是很好的陈礼根」——被叫本名的时候，他反而最乖。','本名梗 · 陈礼根'],['「主打一个事事有回应，事事没着落。」——狼人杀那晚他直接开麦当预言家。','狼人杀名场面']],duo:'你把心事写在卡片上，TA 读不出来；最后是马天宇替你念的，还念得很大声。',theme:'#7f8f8a'}
];

const Q = [
{scene:'01 / 马克杯事件',fact:'情境：一段断联很久的关系，和一件想送又没送出去的东西。',title:'和旧友断联多年，你刷到了一个TA绝对会喜欢的杯子。你的第一反应？',opts:[
['直接下单寄过去，也不提前打招呼。',[2,-1,1,2,1]],
['存进收藏夹，等哪天真的聊上了再说。',[0,1,-1,-1,0]],
['看了两眼就划走，喜欢过的东西不必留个去处。',[-2,2,-1,0,-1]],
['拍张照发过去：“这个你会喜欢，但我没买。”',[2,0,1,0,1]]]},
{scene:'02 / 同框零沟通',fact:'情境：十八天旅程第一天，两个多年没联系的人被安排在同一排。',title:'十八天旅程第一天，你和十年没联系的旧友被安排坐同一排。你会？',opts:[
['先转头打招呼，哪怕只换回一个点头。',[2,-1,2,2,0]],
['戴上耳机看窗外，谁也别为难谁。',[-2,2,-1,-1,-1]],
['等对方先动，开场白在心里排练了七八遍。',[1,-1,-1,0,2]],
['先问一句：“那件事，你想聊还是先放着？”',[1,1,2,1,0]]]},
{scene:'03 / 关系越界预警',fact:'情境：朋友没打招呼，就替你安排了一场“惊喜重逢”。',title:'关系很好的朋友未经商量，就把你安排进一个“惊喜重逢局”。你内心弹幕是？',opts:[
['当场配合把戏演完，散场后再问一句“你怎么想的”。',[2,-1,2,1,1]],
['人到了，但把话说清楚：下次这种事请先问我。',[-1,2,2,0,-1]],
['掉头就走，回家再发一条消息解释。',[-2,2,0,-1,-1]],
['来都来了，先把场面撑住，把人照顾好。',[1,0,1,2,1]]]},
{scene:'04 / 友情唯一性考核',fact:'情境：最要好的朋友带回了新朋友，还说“以后三个人一起”。',title:'朋友们私下聊起你，最可能用哪句话形容你在这类场合的样子？',opts:[
['立刻答应，顺手把三个人拉进一个群。',[1,-1,1,2,-2]],
['笑着应下，回家翻聊天记录找“我们以前更近”的证据。',[0,-1,-1,0,2]],
['回一句“你们玩得开心”，然后不再主动提。',[-1,2,0,0,-2]],
['照实说：我怕我们俩的相处会变，但我想试试。',[1,0,2,0,2]]]},
{scene:'05 / 领队意见不合',fact:'情境：两个曾经很默契的搭档，第一次在路线问题上谈不拢。',title:'两位曾经超有默契的搭档，现在连路线都讨论不拢。你是其中一个，你会？',opts:[
['先按一个人的方案走，错了路上再改。',[1,-1,0,2,1]],
['停下来问：我们在争路线，还是在争谁说了算？',[2,0,2,0,1]],
['分开走，各自玩得舒服比凑在一起重要。',[-2,2,0,-1,-2]],
['把时间、预算、各自想去的地方列出来，按规则定。',[0,2,2,1,-1]]]},
{scene:'06 / 裹毯子落泪与搬行李',fact:'情境：刚吵完架，对方却先替你做了件小事。',title:'刚吵完一架，TA却默默帮你把行李搬回房间。你的第一句是？',opts:[
['接过行李，先说一句“刚才我也有点冲”。',[2,-1,1,2,2]],
['道谢，但把“那件事还没谈完”也放在桌上。',[0,2,2,1,0]],
['请他放下，我现在需要一个人待一会儿。',[-1,2,-1,-2,0]],
['不说话，先去倒杯水，把气氛缓下来。',[1,0,-1,1,1]]]},
{scene:'07 / 迟到的介绍信',fact:'情境：旧友寄来一封很长的信，把过去写得清清楚楚。',title:'这封信在你桌上放了三天。第四天，你做了什么？',opts:[
['读完，认真回一封，也写下自己的版本。',[2,0,2,0,1]],
['读完很触动，但先说清楚：感动不等于我要回头。',[-1,2,1,0,-1]],
['先不回，等自己把情绪安顿好再说。',[-1,1,-2,-1,0]],
['约他当面聊，把信里没写完的那段讲完。',[2,-1,2,2,1]]]},
{scene:'08 / 布达拉宫友情合影',fact:'情境：旅行团第一次拍合照，这张照片要不要发出去。',title:'旅行团终于拍合照了。你在朋友圈发图之前最可能做什么？',opts:[
['原图发群里，谁的丑照都可以留着。',[2,-1,1,2,1]],
['自己悄悄留一张，不必发出去。',[-1,1,-2,-1,1]],
['发一张大家都过得去的，不挑最上镜的。',[-1,2,0,0,-2]],
['先问每个人能不能发，再统一配文。',[2,0,2,1,0]]]},
{scene:'09 / 五人狼人杀游戏局',fact:'情境：一局狼人杀，第一轮你就被朋友投了出去。',title:'被投出去的那一刻，你更接近哪种反应？',opts:[
['笑着认下，先把这一局打完。',[0,0,1,2,-1]],
['当场要理由：你凭什么第一轮就投我？',[-1,1,2,2,-1]],
['喊一句“绝交五分钟”，下一轮又跟他站一边。',[1,-1,1,2,1]],
['游戏结束再说，走，先吃饭去。',[2,0,1,1,1]]]},
{scene:'10 / 后会友期：最后一站',fact:'情境：车快到站了，旧友问“我们以后还会见面吗”。',title:'车要到站了，旧友问你：“我们以后还会见面吗？”你最想回答？',opts:[
['“会。下次我来约。”',[2,-1,2,2,1]],
['“不知道，但这段路走完已经很好。”',[-1,1,0,-1,-1]],
['“先把没说完的说清楚，再谈以后。”',[1,0,2,1,0]],
['“我会记得你，也会继续过我自己的。”',[-2,2,-1,-1,0]]]}
];

const C = Object.fromEntries(characters.map(c => [c.id, c]));

const HOTLINES = [
  ['我画地为牢啊，厉娜。', '出圈句式模板 · 全网都在造句', 'li'],
  ['我等这一刻等了十五年了，厉娜。', '许飞 · 被剪成二创 BGM', 'xu'],
  ['人类好可怕，我要回郊区了。', '马天宇 · 密友数测出零', 'ma'],
  ['释怀了不代表我就要原谅他。', '白小纯 · 课题分离', 'bai'],
  ['白小纯是一本摊开的书，可惜青稚不识字。', '纯稚热梗 · 太好懂也是一种危险', 'bai'],
  ['主打一个事事有回应，事事没着落。', '狼人杀名场面 · 白小纯', 'bai'],
  ['我不想做朋友了。', '王子璇 · 成年人绝交体面学', 'wang'],
  ['友情仅退款。', '文吉儿 · 三万块写序费', 'wen'],
  ['你还记得你喜欢收藏马克杯吗？', '张萌 · 单条 89 万赞名场面', 'zhang'],
  ['不过是山下的人，怎么嘲笑山上的神。', '青稚 · 电竞二创', 'qing'],
  ['明明是很好的陈礼根。', '本名梗 · 白小纯', 'bai'],
  ['老兵烧烤，今天出摊。', '许飞 · 出圈外号', 'xu'],
  ['马天宇不仅识字，还大声念给青稚听。', '代读梗 · 纯稚', 'ma'],
  ['土皇帝。', '青稚 · 老外号', 'qing']
];
const choiceAnchors = {"li":[1,1,2,2,2,1,2,1,3,3],"xu":[3,0,0,3,1,1,0,3,1,0],"zhang":[0,0,0,0,0,3,3,0,0,0],"ma":[2,1,1,2,0,2,1,1,0,1],"wen":[3,2,1,1,1,1,0,2,2,2],"wang":[2,2,0,0,2,3,1,2,0,1],"qing":[0,3,3,0,0,0,3,0,2,1],"bai":[1,3,3,3,3,3,1,3,1,2]};
const answerInsights = {
  0: ['你把“记得”直接落实成动作，先寄出去再说。', '你更愿意先给自己留一点缓冲。', '你珍惜那段过去，但不强迫它重新打开。', '你用一句玩笑试探对方接不接得住。'],
  3: ['你接受新朋友加入，还主动搭了个台。', '你需要确认自己在这段关系里仍然特别。', '你嘴上说没关系，行动上退回了一步。', '你把担心直接说出口，也留了余地。'],
  7: ['你把这份开心先分给所有人。', '你会悄悄收一张属于自己的。', '你不在意这张照片够不够完美。', '你愿意多花点力气让大家都体面。'],
  8: ['你在游戏里不太记仇，先把这一局玩好。', '你遇到质疑先要一个说法。', '你用玩笑把小别扭翻过去。', '你更愿意把场子带回轻松的地方。']
};

/* ---------------- 状态 ---------------- */
const app = document.getElementById('app');
let answers = Array(Q.length).fill(-1);
let step = 0, current = null, selectedTemplate = 'cinema';
let customPhotos = {}, imgCache = {}, portraitFocus = {};
let fromQuiz = false, advancing = false;

const $ = s => document.querySelector(s);
const e = s => String(s).replace(/[&<>"']/g, k => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[k]));

function toast(msg) {
  const t = $('#toast'); if (!t) return;
  t.textContent = msg; t.classList.add('on');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => t.classList.remove('on'), 2800);
}
function nav(dark) {
  return '<div class="nav' + (dark ? ' is-dark' : '') + '">' +
    '<a class="brand" href="' + APP_PATH + '">HOU HUI YOU QI / 后会友期</a>' +
    '<span class="tag">非官方粉丝创作</span></div>';
}

/* ---------------- 首屏 ---------------- */
function streamStrip() {
  const items = ['40 亿播放', '715 个热搜', '我画地为牢啊，厉娜', '白小纯是一本摊开的书', '老兵烧烤出摊了', '土皇帝', '人类好可怕，我要回郊区了', '马天宇不仅识字，还大声念给青稚听'];
  const row = items.map(t => '<i>' + e(t) + '</i>').join('');
  return '<div class="stream" aria-hidden="true"><div class="stream-track">' + row + row + '</div></div>';
}
function castStrip() {
  return '<div class="cast">' + characters.map(function (c, i) {
    return '<figure><span class="cast-no">0' + (i + 1) + '</span>' +
      '<img src="' + e(photoSources[c.id].url) + '" alt="' + e(c.name) + '" loading="lazy" decoding="async" onerror="this.style.visibility=\'hidden\'">' +
      '<figcaption><b>' + e(c.name) + '</b><i>' + e(c.nick) + '</i></figcaption></figure>';
  }).join('') + '</div>';
}
function home() {
  document.title = '谁是你的友情嘴替？｜后会友期 · 友情人物测试';
  document.body.classList.remove('has-bar');
  window.scrollTo(0, 0);
  let hasProgress = false;
  try { hasProgress = !!sessionStorage.getItem('hhyq-progress'); } catch (err) { }
  app.innerHTML =
    '<main class="home">' + nav(true) + streamStrip() +
      '<div class="hero">' +
        '<div class="hero-copy">' +
          '<div class="kicker">Friendship / 友情售后中心</div>' +
          '<h1><span>旧友重逢，</span><span>谁是你的</span><span><em class="ink">互联网嘴替</em>？</span></h1>' +
          '<p class="lead">删了微信，马克杯还记得；想和好，嘴比心硬；关系越界了，先启动门禁。<br>10 道《后会友期》名场面衍生题，测出你更像哪种友情人设。</p>' +
          '<div class="meta"><span>10 题</span><span>约 2 分钟</span><span>8 位原型</span><span>4 款海报</span></div>' +
          '<div class="cta-row">' +
            '<button class="btn" id="start">开始测试 →</button>' +
            (hasProgress ? '<button class="btn btn--light" id="continue">继续上次答题</button>' : '') +
          '</div>' +
          '<p class="legal">非官方粉丝二创：情境取自公开节目片段，人物标签是原创趣味类比，不是嘉宾本人的心理评估。照片可由你自己更换。</p>' +
        '</div>' +
        '<div class="hero-cast">' + castStrip() +
          '<div class="cast-note"><span>八位嘉宾 · 八种友情立场</span><span>SCROLL →</span></div>' +
        '</div>' +
      '</div>' +
    '</main>';
  const strip = $('.cast');
  if (strip) strip.scrollLeft = 0;
  $('#start').onclick = reset;
  const c = $('#continue');
  if (c) c.onclick = () => { if (resume()) renderQuestion(); else { reset(); } };
}

/* ---------------- 答题 ---------------- */
function reset() {
  step = 0; answers = Array(Q.length).fill(-1); fromQuiz = false;
  try { sessionStorage.removeItem('hhyq-progress'); } catch (err) { }
  history.replaceState({}, '', location.pathname);
  renderQuestion();
}
function saveProgress() { try { sessionStorage.setItem('hhyq-progress', JSON.stringify({ answers, step })); } catch (err) { } }
function resume() {
  try {
    const s = JSON.parse(sessionStorage.getItem('hhyq-progress'));
    if (s && Array.isArray(s.answers) && s.answers.length === Q.length && s.answers.every(a => a >= -1 && a < 4)) {
      answers = s.answers; step = Math.max(0, Math.min(Q.length - 1, s.step || 0)); return true;
    }
  } catch (err) { }
  return false;
}

function renderQuestion() {
  document.title = '第' + (step + 1) + '站｜后会友期 · 友情人物测试';
  document.body.classList.remove('has-bar');
  window.scrollTo(0, 0);
  const q = Q[step];
  const ticks = Array.from({ length: Q.length }, (_, i) =>
    '<i class="tick ' + (i < step ? 'on' : i === step ? 'now' : '') + '"></i>').join('');
  app.innerHTML =
    '<main class="shell">' + nav(false) +
      '<div class="route"><div class="route-inner">' +
        '<div class="route-top"><span>友情售后工单 · <strong>第 ' + (step + 1) + ' 站</strong></span><span>' + (step + 1) + ' / ' + Q.length + '</span></div>' +
        '<div class="ticks" role="progressbar" aria-label="答题进度" aria-valuemin="0" aria-valuemax="' + Q.length + '" aria-valuenow="' + (step + 1) + '">' + ticks + '</div>' +
      '</div></div>' +
      '<div class="quiz">' +
        '<div class="stopline"><span>' + e(q.scene) + '</span></div>' +
        '<section class="qcard">' +
          '<div class="qhead"><h2>' + e(q.title) + '</h2>' +
            '<p class="qfact">' + e(q.fact) + '<small>以下为原创情境选项，不是嘉宾在节目中的真实作答。</small></p></div>' +
          '<div class="opts"><div class="opts-inner">' +
            q.opts.map((o, i) =>
              '<button class="opt" data-ans="' + i + '" aria-pressed="' + (answers[step] === i) + '">' +
                '<span class="opt-key">' + ('ABCD'[i]) + '</span><span class="opt-text">' + e(o[0]) + '</span></button>').join('') +
          '</div></div>' +
        '</section>' +
        '<div class="qfoot"><button class="qback" id="back">' + (step ? '← 上一站' : '← 回首页') + '</button>' +
          '<span class="qhint">选完<b>自动</b>进入下一站</span></div>' +
        '<p class="qhint">没有标准答案，第一反应最像你的友情相处方式。</p>' +
      '</div>' +
    '</main>';

  document.querySelectorAll('[data-ans]').forEach(b => b.onclick = () => choose(Number(b.dataset.ans)));
  $('#back').onclick = () => { if (step === 0) home(); else { step--; saveProgress(); renderQuestion(); } };
  document.onkeydown = onKey;
}

function choose(i) {
  if (advancing) return;
  answers[step] = i;
  saveProgress();
  document.querySelectorAll('[data-ans]').forEach(b => {
    const on = Number(b.dataset.ans) === i;
    b.setAttribute('aria-pressed', String(on));
  });
  advancing = true;
  setTimeout(() => { advancing = false; next(); }, 340);
}
function next() {
  if (answers[step] < 0) return;
  if (step === Q.length - 1) {
    current = scoreResult(); fromQuiz = true;
    try { sessionStorage.removeItem('hhyq-progress'); } catch (err) { }
    history.replaceState({}, '', location.pathname + '?r=' + current.id);
    renderResult();
  } else { step++; saveProgress(); renderQuestion(); }
}
function onKey(ev) {
  const k = ev.key.toLowerCase();
  const map = { a: 0, b: 1, c: 2, d: 3, '1': 0, '2': 1, '3': 2, '4': 3 };
  if (map[k] !== undefined) { choose(map[k]); return; }
  if (k === 'arrowright' || k === 'enter') { ev.preventDefault(); next(); }
}

/* ---------------- 计分 ---------------- */
function scoreForTests(a) {
  const totals = [0, 0, 0, 0, 0];
  a.forEach((pick, i) => Q[i].opts[pick][1].forEach((v, j) => totals[j] += v));
  return totals.map(t => Math.max(0, Math.min(100, 50 + t * 2.5)));
}
function scoreResult() {
  const v = scoreForTests(answers);
  const ranking = characters.map(c => {
    const dims = c.dims.reduce((sum, x, k) => sum + (x - v[k]) ** 2 * (k === 4 ? 1.12 : 1), 0) / 50000;
    const picks = answers.reduce((sum, a, k) => sum + (a !== choiceAnchors[c.id][k] ? 1 : 0), 0) / Q.length;
    return { c, dist: .4 * picks + .6 * dims };
  }).sort((a, b) => a.dist - b.dist);
  ranking[0].c.runner = ranking[1].c.name;
  ranking[0].c.match = Math.max(38, Math.min(96, Math.round(100 - ranking[0].dist * 74)));
  return ranking[0].c;
}
function evidenceBlock(c) {
  const real = fromQuiz && answers.every(a => a >= 0 && a < 4) && scoreResult().id === c.id;
  if (!real) {
    return '<p class="note">你正在查看的是人物画像预览。完整答完 10 题后，这里会显示你自己这一轮的选择线索。</p>';
  }
  const picks = [0, 3, 7, 8].map(i => ({ i, match: answers[i] === choiceAnchors[c.id][i], text: answerInsights[i][answers[i]] }));
  const selected = picks.sort((a, b) => Number(b.match) - Number(a.match)).slice(0, 3).sort((a, b) => a.i - b.i);
  return '<div class="evidence">' + selected.map(v =>
    '<div class="ev"><span>第' + (v.i + 1) + '题</span><p>' + e(v.text) + '</p></div>').join('') +
    '</div><p class="note">只是说明这次的选择如何参与趣味匹配，不是科学人格测量。</p>';
}

/* ---------------- 照片 ---------------- */
function getPhotoSrc(id) { return customPhotos[id] || (photoSources[id] && photoSources[id].url) || ''; }
function getFocus(id) { return Math.min(95, Math.max(5, Number(portraitFocus[id] ?? 40))); }
function photoImg(id) {
  const src = getPhotoSrc(id);
  if (!src) return Promise.resolve(null);
  if (imgCache[id] && imgCache[id].src === src) return imgCache[id].promise;
  const promise = new Promise(resolve => {
    const im = new Image();
    if (!src.startsWith('data:')) im.crossOrigin = 'anonymous';
    let done = false;
    const finish = a => { if (done) return; done = true; clearTimeout(timer); resolve(a); };
    im.onload = () => finish(im);
    im.onerror = () => finish(null);
    const timer = setTimeout(() => finish(null), 7000);
    im.src = src;
  });
  imgCache[id] = { src, promise };
  return promise;
}

/* ---------------- 结果 ---------------- */
function resultHTML(c) {
  const meme = c.meme.split('\n');
  const caption = c.caption.split('\n');
  const k = s => s.split('：')[0];
  const v = s => s.split('：').slice(1).join('：');
  return '<main class="result">' + nav(false) +
    '<section class="verdict"><div class="verdict-inner">' +
      '<div class="verdict-head">' +
        '<div class="verdict-eyebrow">Result / 友情嘴替鉴定书</div>' +
        '<h1>' + e(c.name) + '<small>型</small></h1>' +
        '<div class="vtype">' + e(c.title) + '</div>' +
        '<div class="valias"># 网友外号 · ' + e(c.nick) + '</div>' +
        (fromQuiz ? '<div class="vmatch">匹配度 <b>' + c.match + '</b><i>%</i></div>' : '') +
        '<span class="stamp">' + e(c.stamp) + '</span>' +
      '</div>' +
      '<figure class="portrait">' +
        '<div class="portrait-frame"><img id="portrait-img" src="' + e(getPhotoSrc(c.id)) + '" alt="' + e(c.name) + ' 人物照片" crossorigin="anonymous" style="object-position:center ' + getFocus(c.id) + '%" onerror="this.style.opacity=0"></div>' +
        '<div class="figcap"><span>人物照片 / 可更换</span><button class="editlink" id="edit-photo">换成我的图</button></div>' +
      '</figure>' +
      '<div class="verdict-foot">' +
        (fromQuiz && c.runner ? '<span class="runner">最接近的第二位：<b>' + e(c.runner) + '</b></span>' : '') +
        '<div class="verdict-actions">' +
          '<button class="btn" id="go-poster">生成我的海报</button>' +
          '<button class="btn btn--light" id="share-link">分享结果</button>' +
        '</div>' +
        '<p class="legal">你不是被判定为某位真人。结果是一种友情处境下的原型类比，不是心理评估。</p>' +
      '</div>' +
    '</div></section>' +

    '<div class="read">' +
      '<section class="sec"><div class="sec-label">01 <b>你的互联网弹幕</b></div>' +
        '<div class="bubble">' + e(meme[0]) + (meme[1] ? '<em>' + e(meme[1]) + '</em>' : '') + '</div></section>' +
      '<section class="sec"><div class="sec-label">02 <b>表面与内心两套系统</b></div>' +
        '<div class="pair">' +
          '<div><k>' + e(k(caption[0])) + '</k><span>' + e(v(caption[0])) + '</span></div>' +
          (caption[1] ? '<div><k>' + e(k(caption[1])) + '</k><span>' + e(v(caption[1])) + '</span></div>' : '') +
        '</div></section>' +
      '<section class="sec"><div class="sec-label">03 <b>你的选择怎么算出来的</b></div>' + evidenceBlock(c) + '</section>' +
      '<section class="sec"><div class="sec-label">04 <b>说点真正戳心的</b></div><p class="prose">' + e(c.touch) + '</p></section>' +
      '<section class="sec"><div class="sec-label">05 <b>友情翻车预警</b></div><p class="warn">' + e(c.weak) + '</p></section>' +
      '<section class="sec"><div class="sec-label">06 <b>下一站小纸条</b></div><p class="pull">' + e(c.mission.replace('你的友情通关提示：', '')) + '</p>' +
        '<div class="scene"><b>节目对应情境：</b>' + e(c.scenetitle.replace('节目对应：', '')) +
          '<br><a href="' + e(c.scenesrc) + '" target="_blank" rel="noopener noreferrer">查看芒果TV节目资料 ↗</a>' +
          '<br>人物标签与梗文案均为原创趣味类比，不是嘉宾真实发言，也不是科学测评。</div>' +
        '<div class="sec-actions"><button class="btn btn--dark btn--sm" id="poster-cta">选海报 ↓</button>' +
          '<button class="btn btn--ghost btn--sm" id="share-2">分享结果</button>' +
          '<button class="btn btn--ghost btn--sm" id="restart">再测一次</button></div>' +
      '<section class="sec"><div class="sec-label">07 <b>全网都在刷的梗</b></div>' +
        '<div class="memewall">' +
          '<div class="meme meme--own"><span class="meme-tag">网友外号 · ' + e(c.nick) + '</span>' +
            c.hots.map(function (h) {
              return '<p>' + e(h[0]) + '</p><span class="meme-src">' + e(h[1]) + '</span>';
            }).join('') + '</div>' +
          HOTLINES.filter(function (h) { return h[2] !== c.id; }).slice(0, 4).map(function (h) {
            return '<div class="meme"><p>' + e(h[0]) + '</p><span class="meme-src">' + e(h[1]) + '</span></div>';
          }).join('') +
          '<div class="meme meme--duo"><span class="meme-tag">你们这对 · ' + e(c.pair) + '</span><p>' + e(c.duo) + '</p></div>' +
          '<p class="meme-note">以上均为网友对节目内容的二创玩梗，不是嘉宾本人发言，也不构成对真实性格的判断。</p>' +
        '</div></section>' +
      '</section>' +
    '</div>' +

    '<section class="poster" id="poster-chooser"><div class="poster-inner">' +
      '<h2>挑一张你愿意发出去的海报</h2>' +
      '<p class="sub">四款是不同的版式，不是换色。点一下就能预览，选好后保存成 1080×1920 的图片。</p>' +
      '<div class="tmpl-grid">' + templates.map(t =>
        '<button class="tmpl" data-template="' + t.id + '" aria-pressed="' + (t.id === selectedTemplate) + '">' +
          '<canvas id="canvas-' + t.id + '" width="270" height="480" aria-label="' + e(t.name) + ' 海报预览"></canvas>' +
          '<div class="tmpl-label"><strong>' + e(t.name) + '</strong><em>' + e(t.desc) + '</em></div>' +
        '</button>').join('') + '</div>' +
      '<div class="tools">' +
        '<button class="btn btn--dark" id="download">保存这张海报 ↓</button>' +
        '<select class="sel" id="character-preview" aria-label="预览其他角色">' +
          characters.map(p => '<option value="' + p.id + '"' + (p.id === c.id ? ' selected' : '') + '>预览 · ' + e(p.name) + '</option>').join('') +
        '</select>' +
        '<button class="btn btn--ghost" id="copy-caption">复制朋友圈文案</button>' +
      '</div>' +
      '<details class="tune"><summary>调整照片 / 重新上传</summary>' +
        '<div class="tune-body">' +
          '<label class="focus" for="photo-focus">照片上下位置<input type="range" min="5" max="95" step="1" id="photo-focus" value="' + getFocus(c.id) + '" aria-label="照片垂直位置"><output id="photo-focus-value">' + getFocus(c.id) + '%</output></label>' +
          '<button class="btn btn--ghost btn--sm" id="upload-button">上传我自己的照片</button>' +
        '</div>' +
      '</details>' +
      '<div class="legalbox">' +
        '<b>关于照片</b>八位人物的默认照片是网站公共资源，别人打开也能看到；你自己上传的照片只保存在本设备，不会替换别人看到的版本。本站非官方，未将官方发布标为开放许可。' +
        '<b>关于结果</b>情境取自公开节目片段，人物标签与文案为原创类比；不代表嘉宾真实人格或真实发言。' +
      '</div>' +
    '</div></section>' +

    '<footer class="foot"><div class="foot-inner">' +
      '<span>《后会友期》非官方粉丝互动作品 · 题目参考芒果TV公开节目情境 · 结果为原创设定</span>' +
      '<span>节目资料：<a href="' + EVIDENCE + '" target="_blank" rel="noopener noreferrer">芒果TV官方节目页</a></span>' +
      '<span id="image-credit"></span>' +
    '</div></footer>' +

    '<div class="bar is-on" id="result-bar">' +
      '<button class="btn" id="bar-poster">保存海报</button>' +
      '<button class="btn btn--dark" id="bar-share">分享结果</button>' +
    '</div>' +
    '<input hidden id="photo-upload" type="file" accept="image/jpeg,image/png,image/webp">' +
  '</main>';
}

function renderResult() {
  if (!current) return home();
  document.title = '我是' + current.name + '型友情嘴替｜后会友期人物测试';
  document.body.classList.add('has-bar');
  window.scrollTo(0, 0);
  app.innerHTML = resultHTML(current);

  const toPoster = () => document.getElementById('poster-chooser').scrollIntoView({ behavior: 'smooth', block: 'start' });
  $('#go-poster').onclick = toPoster;
  $('#poster-cta').onclick = toPoster;
  $('#bar-poster').onclick = () => download();
  $('#share-link').onclick = share;
  $('#share-2').onclick = share;
  $('#bar-share').onclick = share;
  $('#restart').onclick = reset;
  $('#download').onclick = download;
  $('#copy-caption').onclick = copyCaption;
  $('#upload-button').onclick = () => $('#photo-upload').click();
  $('#edit-photo').onclick = () => { const t = $('.tune'); if (t) { t.open = true; t.scrollIntoView({ behavior: 'smooth', block: 'center' }); } $('#photo-upload').click(); };
  $('#photo-upload').onchange = handleUpload;

  document.querySelectorAll('[data-template]').forEach(x => x.onclick = () => {
    selectedTemplate = x.dataset.template;
    try { localStorage.setItem('hhyq-template', selectedTemplate); } catch (err) { }
    document.querySelectorAll('[data-template]').forEach(y => y.setAttribute('aria-pressed', String(y === x)));
    toast('已选中' + templates.find(t => t.id === selectedTemplate).name);
  });
  $('#character-preview').onchange = ev => {
    current = C[ev.target.value]; fromQuiz = false;
    history.replaceState({}, '', location.pathname + '?r=' + current.id);
    renderResult();
  };
  $('#photo-focus').oninput = ev => {
    const val = Number(ev.target.value);
    portraitFocus[current.id] = val;
    $('#photo-focus-value').textContent = val + '%';
    try { localStorage.setItem('hhyq-focus', JSON.stringify(portraitFocus)); } catch (err) { }
    const im = $('#portrait-img'); if (im) im.style.objectPosition = 'center ' + val + '%';
    drawPreviews();
  };

  const credit = photoSources[current.id];
  if (credit && !customPhotos[current.id]) $('#image-credit').textContent = '默认照片：' + credit.credit;
  drawPreviews();
}

/* ---------------- 分享 / 文件 ---------------- */
function fallbackCopy(text) {
  const ta = document.createElement('textarea');
  ta.value = text; ta.style.position = 'absolute'; ta.style.left = '-9999px';
  document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove();
}
async function copyText(text) {
  try { await navigator.clipboard.writeText(text); } catch (err) { fallbackCopy(text); }
}
function copyCaption() {
  copyText('我测出了《后会友期》里的「' + current.name + '」型友情嘴替——' + current.title + '。\n' +
    current.stamp + '\n不是我对号入座，是这档节目在我心里装监控了。\n你测出谁？ ' + APP_PATH)
    .then(() => toast('朋友圈文案已复制'));
}
async function share() {
  const text = '我测出了《后会友期》友情嘴替：' + current.title + '。你也来测测！';
  const url = APP_PATH + '?r=' + current.id;
  try {
    if (navigator.share) await navigator.share({ title: '谁是你的友情嘴替？', text, url });
    else { await copyText(text + '\n' + url); toast('结果链接已复制'); }
  } catch (err) {
    if (err.name !== 'AbortError') { await copyText(text + '\n' + url); toast('结果链接已复制'); }
  }
}

function dbOpen() {
  return new Promise((resolve, reject) => {
    if (!window.indexedDB) return reject(Error('No DB'));
    const r = indexedDB.open('hhyq-photos', 1);
    r.onupgradeneeded = () => r.result.createObjectStore('pictures');
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(r.error);
  });
}
async function savePhoto(id, s) {
  try {
    const db = await dbOpen();
    await new Promise((resolve, reject) => {
      const t = db.transaction('pictures', 'readwrite');
      t.objectStore('pictures').put(s, id);
      t.oncomplete = resolve; t.onerror = () => reject(t.error);
    });
    db.close();
  } catch (err) { toast('图片已用于当前页面，但浏览器未允许本地保存'); }
}
async function restorePhotos() {
  try {
    const db = await dbOpen();
    const values = await Promise.all(characters.map(p => new Promise(res => {
      const t = db.transaction('pictures');
      const req = t.objectStore('pictures').get(p.id);
      req.onsuccess = () => res([p.id, req.result]);
      req.onerror = () => res([p.id, null]);
    })));
    for (const [id, uri] of values) if (uri) customPhotos[id] = uri;
    db.close();
  } catch (err) { }
}
function compressFile(file) {
  return new Promise((resolve, reject) => {
    const fr = new FileReader();
    fr.onerror = () => reject(Error('read'));
    fr.onload = () => {
      const im = new Image();
      im.onerror = () => reject(Error('image'));
      im.onload = () => {
        const r = Math.min(1, 1350 / Math.max(im.width, im.height));
        const cv = document.createElement('canvas');
        cv.width = Math.max(1, Math.round(im.width * r));
        cv.height = Math.max(1, Math.round(im.height * r));
        const ctx = cv.getContext('2d');
        ctx.drawImage(im, 0, 0, cv.width, cv.height);
        resolve(cv.toDataURL('image/jpeg', .88));
      };
      im.src = fr.result;
    };
    fr.readAsDataURL(file);
  });
}
async function handleUpload(ev) {
  const file = ev.target.files && ev.target.files[0];
  if (!file) return;
  if (!file.type.startsWith('image/')) return toast('请选择照片文件');
  if (file.size > 18 * 1024 * 1024) return toast('请使用小于 18MB 的图片');
  try {
    const uri = await compressFile(file);
    customPhotos[current.id] = uri;
    delete imgCache[current.id];
    await savePhoto(current.id, uri);
    renderResult();
    toast('照片已更新，并应用到四款海报');
  } catch (err) { toast('照片读取失败，请换一张图片'); }
}

/* ---------------- 海报绘制 ---------------- */
const FSERIF = '"Songti SC","STSong","Source Han Serif SC","Noto Serif SC",serif';
const FSANS = '-apple-system,"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif';
const FMONO = 'ui-monospace,"SF Mono",Menlo,monospace';
const INK = '#12242F', NIGHT = '#0B1E2B', CREAM = '#F2E8D8', PAPER = '#FBF5EA', AMBER = '#D9A05B', DUST = '#6E8087';

let qrLib = null;
function ensureQR() {
  if (window.qrcode) { qrLib = window.qrcode; return Promise.resolve(true); }
  return new Promise(resolve => {
    const s = document.createElement('script');
    s.src = './qrcode.js'; s.async = true;
    s.onload = () => { qrLib = window.qrcode; resolve(!!qrLib); };
    s.onerror = () => resolve(false);
    document.head.appendChild(s);
  });
}
function drawQR(ctx, url, x, y, size, dark, light) {
  if (!qrLib) return false;
  try {
    const qr = qrLib(0, 'M');
    qr.addData(url);
    qr.make();
    const n = qr.getModuleCount();
    const cell = size / (n + 4);
    ctx.fillStyle = light;
    ctx.fillRect(x, y, size, size);
    ctx.fillStyle = dark;
    for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) {
      if (qr.isDark(r, c)) ctx.fillRect(x + cell * (c + 2), y + cell * (r + 2), cell + .35, cell + .35);
    }
    return true;
  } catch (err) { return false; }
}

function rr(ctx, x, y, w, h, r, fill) {
  ctx.fillStyle = fill;
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect(x, y, w, h, r); else ctx.rect(x, y, w, h);
  ctx.fill();
}
function font(ctx, size, family, weight) { ctx.font = (weight || '400') + ' ' + size + 'px ' + family; }
function text(ctx, str, x, y, opt) {
  opt = opt || {};
  font(ctx, opt.size || 24, opt.family || FSERIF, opt.weight);
  ctx.fillStyle = opt.color || INK;
  const ls = opt.ls || 0;
  if (ls) {
    let cx = x;
    for (const ch of str) { ctx.fillText(ch, cx, y); cx += ctx.measureText(ch).width + ls; }
  } else ctx.fillText(str, x, y);
}
function spaced(ctx, str, x, y, size, color, ls, family) {
  font(ctx, size, family || FMONO, '400');
  ctx.fillStyle = color;
  let cx = x;
  for (const ch of str) { ctx.fillText(ch, cx, y); cx += ctx.measureText(ch).width + ls; }
}
/* 中文按字断行，避免标点出现在行首 */
function wrapCJK(ctx, str, width, maxLines) {
  const lines = [];
  let line = '';
  for (const ch of str) {
    if (ch === '\n') { lines.push(line); line = ''; continue; }
    const test = line + ch;
    if (ctx.measureText(test).width > width && line) {
      if ('，。、）」！？：；·'.includes(ch) && line.length > 1) {
        lines.push(line.slice(0, -1));
        line = line.slice(-1) + ch;
      } else { lines.push(line); line = ch; }
    } else line = test;
    if (lines.length >= maxLines) break;
  }
  if (line && lines.length < maxLines) lines.push(line);
  return lines;
}
function block(ctx, str, x, y, width, size, color, family, weight, lh, maxLines) {
  font(ctx, size, family || FSANS, weight);
  ctx.fillStyle = color;
  const lines = wrapCJK(ctx, str, width, maxLines || 4);
  lines.forEach((l, i) => ctx.fillText(l, x, y + i * (lh || size * 1.5)));
  return lines.length;
}
function cover(ctx, img, x, y, w, h, focusPct) {
  const sc = Math.max(w / img.naturalWidth, h / img.naturalHeight);
  const sw = img.naturalWidth * sc, sh = img.naturalHeight * sc;
  const f = (focusPct === undefined ? 40 : focusPct) / 100;
  ctx.drawImage(img, x + (w - sw) / 2, y - Math.max(0, sh - h) * f, sw, sh);
}
function photo(ctx, img, x, y, w, h, c) {
  ctx.save();
  ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip();
  if (img) cover(ctx, img, x, y, w, h, getFocus(c.id));
  else artFallback(ctx, x, y, w, h, c);
  ctx.restore();
}
function artFallback(ctx, x, y, w, h, c) {
  const g = ctx.createLinearGradient(x, y, x + w, y + h);
  g.addColorStop(0, '#8CA0A2'); g.addColorStop(.55, c.theme); g.addColorStop(1, '#16303E');
  ctx.fillStyle = g; ctx.fillRect(x, y, w, h);
  ctx.fillStyle = 'rgba(226,169,104,.7)';
  ctx.beginPath(); ctx.arc(x + w * .74, y + h * .24, Math.min(w, h) * .12, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#0F2735';
  ctx.beginPath(); ctx.moveTo(x, y + h * .72); ctx.lineTo(x + w * .36, y + h * .4); ctx.lineTo(x + w * .56, y + h * .64);
  ctx.lineTo(x + w * .8, y + h * .38); ctx.lineTo(x + w, y + h * .62); ctx.lineTo(x + w, y + h); ctx.lineTo(x, y + h); ctx.fill();
  text(ctx, c.name, x + 40, y + h * .82, { size: 96, color: '#FFF1D8', ls: 6 });
  font(ctx, 18, FSANS); ctx.fillStyle = '#E3CBAA';
  ctx.fillText('上传照片即可替换这张字卡', x + 42, y + h * .89);
}
function scrim(ctx, x, y, w, h, from, to) {
  const g = ctx.createLinearGradient(0, y, 0, y + h);
  g.addColorStop(0, from); g.addColorStop(1, to);
  ctx.fillStyle = g; ctx.fillRect(x, y, w, h);
}
function barcode(ctx, x, y, w, h, seedStr, color) {
  ctx.fillStyle = color;
  let hseed = 7;
  for (const ch of seedStr) hseed = (hseed * 31 + ch.charCodeAt(0)) % 9973;
  let cx = x;
  while (cx < x + w) {
    hseed = (hseed * 1103515245 + 12345) % 2147483647;
    const bar = 1 + (hseed % 4);
    if (hseed % 3 !== 0) ctx.fillRect(cx, y, bar, h);
    cx += bar + 1 + (hseed % 3);
  }
}

function drawPoster(cvs, c, img, t, qrReady) {
  const ctx = cvs.getContext('2d');
  const W = 900, H = 1600;
  ctx.setTransform(cvs.width / W, 0, 0, cvs.height / H, 0, 0);
  ctx.clearRect(0, 0, W, H);
  const focus = getFocus(c.id);

  if (t === 'cinema') {
    /* 一张电影帧：照片满版，字压在影像上 */
    ctx.fillStyle = NIGHT; ctx.fillRect(0, 0, W, H);
    if (img) cover(ctx, img, 0, 0, W, H, 30); else artFallback(ctx, 0, 0, W, H, c);
    scrim(ctx, 0, H * .34, W, H * .66, 'rgba(6,18,26,0)', 'rgba(6,18,26,.95)');
    ctx.globalAlpha = .22; ctx.fillStyle = NIGHT; ctx.fillRect(0, 0, W, H * .28); ctx.globalAlpha = 1;

    spaced(ctx, 'HOU HUI YOU QI', 66, 96, 20, '#F0DCC2', 5, FMONO);
    spaced(ctx, 'FRIENDSHIP / 2026', 66, 130, 17, 'rgba(240,220,194,.7)', 4, FMONO);
    ctx.strokeStyle = 'rgba(240,220,194,.34)'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(66, 156); ctx.lineTo(W - 66, 156); ctx.stroke();

    /* 取景框四角 */
    ctx.strokeStyle = 'rgba(240,220,194,.5)'; ctx.lineWidth = 2;
    const m = 34, L = 26;
    [[m, m], [W - m, m], [m, H - m], [W - m, H - m]].forEach(([x, y], i) => {
      ctx.beginPath();
      ctx.moveTo(x + (i % 2 ? -L : L), y); ctx.lineTo(x, y); ctx.lineTo(x, y + (i < 2 ? L : -L));
      ctx.stroke();
    });

    text(ctx, c.name, 62, 1014, { size: 128, color: '#FFF4E2', ls: 8 });
    spaced(ctx, 'YOUR FRIENDSHIP TYPE', 66, 1082, 17, 'rgba(217,160,91,.95)', 4, FMONO);
    block(ctx, c.title, 66, 1156, 730, 36, '#F4E3C8', FSANS, '600', 54, 2);
    block(ctx, c.stamp, 66, 1298, 660, 40, '#F6E7CE', FSERIF, '400', 58, 2);
    ctx.strokeStyle = 'rgba(217,160,91,.8)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(66, 1428); ctx.lineTo(220, 1428); ctx.stroke();
    spaced(ctx, '#后会友期  #友情嘴替', 66, 1484, 20, '#E9D3B4', 1, FSANS);
    spaced(ctx, '非官方粉丝测试 · 不代表嘉宾真实人格', 66, 1534, 15, 'rgba(233,211,180,.66)', 0, FSANS);
  }

  else if (t === 'ticket') {
    /* 一张车票：虚线撕口 + 序列号 + 二维码 */
    ctx.fillStyle = '#E4D8C3'; ctx.fillRect(0, 0, W, H);
    const bx = 44, by = 40, bw = W - 88, bh = H - 80;
    ctx.save();
    ctx.shadowColor = 'rgba(24,38,48,.28)'; ctx.shadowBlur = 34; ctx.shadowOffsetY = 14;
    rr(ctx, bx, by, bw, bh, 26, PAPER);
    ctx.restore();

    ctx.strokeStyle = '#B39577'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.roundRect ? ctx.roundRect(bx + 14, by + 14, bw - 28, bh - 28, 18) : ctx.rect(bx + 14, by + 14, bw - 28, bh - 28); ctx.stroke();

    spaced(ctx, 'FRIENDSHIP EXPRESS', 82, 118, 22, INK, 5, FMONO);
    font(ctx, 24, FSERIF); ctx.fillStyle = '#A88355';
    ctx.fillText('友情车票', 82, 158);
    const serial = 'No. ' + ('000' + (characters.findIndex(x => x.id === c.id) + 1)).slice(-3) + ' / 10 STOPS';
    font(ctx, 17, FMONO); ctx.fillStyle = DUST;
    ctx.textAlign = 'right'; ctx.fillText(serial, W - 84, 156); ctx.textAlign = 'left';

    ctx.fillStyle = 'rgba(18,36,47,.12)'; ctx.fillRect(82, 186, W - 164, 1);

    photo(ctx, img, 82, 214, W - 164, 640, c);

    text(ctx, '旅客姓名 / PASSENGER', 82, 920, { size: 17, family: FMONO, color: '#A88355', ls: 2 });
    text(ctx, c.name, 82, 1030, { size: 112, color: INK, ls: 8 });
    block(ctx, c.title, 84, 1092, W - 200, 32, '#39505C', FSANS, '600', 48, 2);
    block(ctx, c.stamp, 84, 1180, W - 190, 30, '#A88355', FSERIF, '400', 44, 2);

    /* 撕口 */
    const ty = 1246;
    ctx.strokeStyle = 'rgba(18,36,47,.3)'; ctx.lineWidth = 2;
    ctx.setLineDash([12, 10]);
    ctx.beginPath(); ctx.moveTo(bx + 14, ty); ctx.lineTo(bx + bw - 14, ty); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#E4D8C3';
    ctx.beginPath(); ctx.arc(bx, ty, 22, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.arc(bx + bw, ty, 22, 0, Math.PI * 2); ctx.fill();

    /* 存根：二维码放在这里 */
    spaced(ctx, 'DESTINATION', 84, 1310, 16, DUST, 3, FMONO);
    block(ctx, '下一站：把话说完，再各自好好走', 84, 1360, 470, 29, INK, FSERIF, '400', 44, 2);
    spaced(ctx, '2026 · SZX → 后会友期', 84, 1462, 16, '#8B9498', 1, FSANS);
    if (qrReady) {
      drawQR(ctx, APP_PATH, W - 268, 1292, 168, INK, PAPER);
      spaced(ctx, '扫码测你的嘴替', W - 268, 1486, 13, DUST, 0, FSANS);
    }
    spaced(ctx, '非官方粉丝创作 · 票据仅供收藏', 84, 1516, 13, '#96907F', 0, FSANS);
    if (img) spaced(ctx, '人物照片由网站维护者提供', W - 296, 1516, 12, '#96907F', 0, FSANS);
  }

  else if (t === 'magazine') {
    /* 一期特刊：刊头 + 封面标题 + 条形码 */
    ctx.fillStyle = '#F7F0E2'; ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = 'rgba(18,36,47,.16)'; ctx.lineWidth = 2;
    ctx.strokeRect(30, 30, W - 60, H - 60);

    text(ctx, '友情人物', 54, 138, { size: 78, color: INK, ls: 6 });
    font(ctx, 20, FMONO); ctx.fillStyle = '#A88355';
    ctx.textAlign = 'right'; ctx.fillText('VOL.08 / 2026', W - 56, 104); ctx.textAlign = 'left';
    spaced(ctx, 'THE FRIENDSHIP ISSUE', W - 56 - 218, 136, 13, DUST, 2, FMONO);

    ctx.fillStyle = INK; ctx.fillRect(54, 168, W - 108, 3);

    photo(ctx, img, 54, 190, W - 108, 900, c);
    scrim(ctx, 54, 780, W - 108, 310, 'rgba(8,20,28,0)', 'rgba(8,20,28,.9)');
    text(ctx, c.name, 82, 984, { size: 124, color: '#FFF6E6', ls: 6 });
    spaced(ctx, 'COVER STORY / 友情角色特刊', 84, 1048, 15, '#E7C08C', 4, FMONO);

    block(ctx, c.title, 54, 1170, W - 150, 42, INK, FSERIF, '400', 60, 2);
    block(ctx, c.stamp, 54, 1272, W - 170, 30, '#7C8B93', FSANS, '400', 46, 2);

    ctx.fillStyle = 'rgba(18,36,47,.14)'; ctx.fillRect(54, 1332, W - 108, 1);
    ['# 边界先于和解', '# 慢热但记得', '# 可以体面告别'].forEach((tline, i) => {
      if (!c.tags[i]) return;
      spaced(ctx, '# ' + c.tags[i], 54, 1380 + i * 34, 19, '#5D6C72', 1, FSANS);
    });
    barcode(ctx, W - 260, 1400, 200, 54, c.id + c.name, INK);
    spaced(ctx, '非官方 · 由粉丝制作', 54, 1520, 15, DUST, 0, FSANS);
    spaced(ctx, '¥ 0.00 / FAN EDITION', W - 260, 1490, 12, DUST, 0, FMONO);
  }

  else {
    /* 评论区：像一张弹幕截图，卡片高度先量后画，字多时自动降一档 */
    ctx.fillStyle = NIGHT; ctx.fillRect(0, 0, W, H);
    const g = ctx.createLinearGradient(0, 0, W, H);
    g.addColorStop(0, 'rgba(217,160,91,.18)'); g.addColorStop(.6, 'rgba(217,160,91,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);

    spaced(ctx, '# 后会友期 · 友谊弹幕区', 56, 106, 21, '#EFD5B0', 2, FSANS);
    spaced(ctx, '9.2 万人在看', 56, 144, 16, '#8FA3AA', 0, FMONO);

    const cardX = 48, cardW = W - 96, cardTop = 156, padX = 34;
    const innerW = cardW - padX * 2;
    const crowdTxt = '路人：「' + (HOTLINES.filter(function (h) { return h[2] !== c.id; })[0][0]) + '」';
    const replyTxt = c.mission.replace('你的友情通关提示：', '');
    const avail = H - cardTop - 300;

    const plan = (compact, withCrowd) => {
      const fs = compact ? 26 : 31, blh = compact ? 40 : 48, flh = compact ? 38 : 46;
      const pTop = compact ? 38 : 46, pBot = compact ? 20 : 26, gap = compact ? 12 : 18;
      const rows = [];
      c.meme.split('\n').forEach(line => {
        const who = line.split('：')[0];
        const txt = line.slice(who.length + 1);
        font(ctx, fs, FSANS, '600');
        const n = wrapCJK(ctx, txt, innerW - 44, 2).length;
        rows.push({ kind: 'meme', label: who, txt, n, h: pTop + n * blh + pBot });
      });
      font(ctx, compact ? 25 : 30, FSANS, '600');
      const fn = wrapCJK(ctx, c.weak, innerW - 44, 3).length;
      rows.push({ kind: 'friend', label: '朋友', txt: c.weak, n: fn, h: pTop + fn * flh + pBot });
      const rn = wrapCJK(ctx, replyTxt, innerW - 44, 3).length;
      rows.push({ kind: 'reply', label: '楼主回复', txt: replyTxt, n: rn, h: pTop + rn * flh + pBot });
      font(ctx, 20, FSANS, '400');
      const cn = withCrowd ? wrapCJK(ctx, crowdTxt, innerW - 44, 2).length : 0;
      const crowdH = withCrowd ? 40 + cn * 34 : 0;
      const body = rows.reduce((sum, r) => sum + r.h + gap, 0) +
        (withCrowd ? crowdH + 34 : 0) + 16;
      const contentH = 44 + 102 + body;
      return { fs, blh, flh, pTop, pBot, gap, rows, crowdH, withCrowd, contentH };
    };

    const reserve = 300;                     /* 卡片底部留给标题、盖章、入口的高度 */
    let P = plan(false, true);
    if (P.contentH > avail - reserve) P = plan(true, true);
    if (P.contentH > avail - reserve) P = plan(true, false);
    const cardH = avail;                     /* 卡片始终撑到底，避免头重脚轻 */
    const spare = Math.max(0, avail - reserve - P.contentH);
    const extra = Math.min(22, spare / (P.rows.length + 1));
    P.gap += extra;

    rr(ctx, cardX, cardTop, cardW, cardH, 28, PAPER);

    let cy = cardTop + 44;
    const av = 68;
    ctx.save();
    ctx.beginPath(); ctx.arc(cardX + padX + av / 2, cy + av / 2, av / 2, 0, Math.PI * 2); ctx.clip();
    if (img) cover(ctx, img, cardX + padX, cy, av, av, focus); else artFallback(ctx, cardX + padX, cy, av, av, c);
    ctx.restore();
    spaced(ctx, c.name, cardX + padX + av + 18, cy + 32, 20, INK, 1, FSANS);
    spaced(ctx, '楼主 · 刚刚', cardX + padX + av + 18, cy + 58, 13, DUST, 0, FMONO);
    cy += 102;

    P.rows.forEach(r => {
      const bg = r.kind === 'reply' ? '#F6E4C9' : '#EDE3D2';
      const lb = r.kind === 'meme' ? '#A88355' : '#7C8B93';
      rr(ctx, cardX + padX, cy, innerW, r.h, 18, bg);
      spaced(ctx, r.label, cardX + padX + 22, cy + P.pTop - 6, 14, lb, 1, FSANS);
      const lh = r.kind === 'meme' ? P.blh : P.flh;
      block(ctx, r.txt, cardX + padX + 22, cy + P.pTop + 50, innerW - 44, P.fs, INK, FSANS, '600', lh, 3);
      cy += r.h + P.gap;
    });

    if (P.withCrowd) {
      rr(ctx, cardX + padX, cy, innerW, P.crowdH, 18, 'rgba(18,36,47,.06)');
      block(ctx, crowdTxt, cardX + padX + 22, cy + 46, innerW - 44, 20, '#5D6C72', FSANS, '400', 34, 2);
      cy += P.crowdH + 34;
    }

    spaced(ctx, '♡ 2.8w     ↻ 6412     💬 302', cardX + padX, cy, 18, '#8B9498', 1, FSANS);
    cy += 16;
    ctx.strokeStyle = 'rgba(18,36,47,.13)'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(cardX + padX, cy); ctx.lineTo(cardX + cardW - padX, cy); ctx.stroke();

    /* 标题、盖章、评论区入口依次排在卡片底部 */
    const cardBottom = cardTop + cardH;
    text(ctx, c.title, cardX + padX, cardBottom - 214, { size: 38, color: INK, ls: 1 });
    block(ctx, c.stamp, cardX + padX, cardBottom - 158, innerW - 40, 25, '#A88355', FSERIF, '400', 38, 2);
    rr(ctx, cardX + padX, cardBottom - 96, innerW, 46, 23, 'rgba(18,36,47,.05)');
    spaced(ctx, '查看全部 302 条评论  ›', cardX + padX + (innerW - 21 * 9) / 2, cardBottom - 66, 14, '#7C8B93', 1, FSANS);

    /* 页面底部：细线 + 标签 + 二维码，全部收在画布内 */
    const baseY = H - 196;
    ctx.strokeStyle = 'rgba(242,232,216,.18)'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(56, baseY); ctx.lineTo(W - 56, baseY); ctx.stroke();
    spaced(ctx, '#后会友期  #友情售后中心', 56, baseY + 58, 20, '#E7C9A4', 1, FSANS);
    spaced(ctx, '非官方粉丝玩梗 · 不代表嘉宾真实发言', 56, baseY + 96, 13, '#9FB0B4', 0, FSANS);
    if (qrReady) {
      drawQR(ctx, APP_PATH, W - 196, baseY + 20, 118, '#F2E8D8', NIGHT);
      spaced(ctx, '扫码测你的友情嘴替', W - 196, baseY + 152, 11, '#9FB0B4', 0, FSANS);
    }
  }
}

let qrPromise = null;
async function drawPreviews() {
  if (!current) return;
  const c = current, id = c.id;
  if (!qrPromise) qrPromise = ensureQR().then(ok => { if (ok) drawPreviews(); });
  const qrReady = !!qrLib;

  for (const t of templates) {
    const cvs = document.getElementById('canvas-' + t.id);
    if (cvs) drawPoster(cvs, c, null, t.id, qrReady);
  }
  const im = await photoImg(id);
  if (!current || current.id !== id) return;
  for (const t of templates) {
    const cvs = document.getElementById('canvas-' + t.id);
    if (cvs) drawPoster(cvs, c, im, t.id, qrReady);
  }
}

/* ---------------- 保存 ---------------- */
function mobileSaveMode() {
  const ua = navigator.userAgent || '';
  return /iPad|iPhone|iPod|MicroMessenger/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
}
function showPosterSaveSheet(blob, filename, canvas) {
  const old = document.getElementById('poster-sheet'); if (old) old.remove();
  const url = URL.createObjectURL(blob);
  const mask = document.createElement('div');
  mask.className = 'sheet'; mask.id = 'poster-sheet';
  mask.innerHTML =
    '<section class="sheet-dialog" role="dialog" aria-modal="true" aria-label="保存友情海报">' +
      '<div class="sheet-head"><strong>海报做好了</strong><button type="button" id="sheet-close" aria-label="关闭">✕</button></div>' +
      '<p>在 iPhone 或微信里，<b>长按下面这张图 → 保存到相册</b>。也可以点「系统分享」或「下载原图」。</p>' +
      '<div class="sheet-preview"><img id="sheet-img" alt="已生成的友情人物海报，可长按保存"></div>' +
      '<div class="sheet-actions"><button class="btn btn--dark" id="sheet-share">系统分享 / 存储</button>' +
      '<a class="btn btn--ghost" id="sheet-file" download="' + e(filename) + '">下载原图</a></div>' +
      '<small>如果微信限制了保存，可以用浏览器打开，或直接截图保留海报。</small>' +
    '</section>';
  document.body.appendChild(mask);

  const preview = mask.querySelector('.sheet-preview');
  canvas.className = 'sheet-canvas';
  preview.prepend(canvas);
  const picture = mask.querySelector('#sheet-img');
  picture.src = url;
  picture.onerror = () => { picture.onerror = null; picture.src = canvas.toDataURL('image/png'); };
  mask.querySelector('#sheet-file').href = url;

  const close = () => { URL.revokeObjectURL(url); mask.remove(); document.removeEventListener('keydown', esc); };
  function esc(ev) { if (ev.key === 'Escape') close(); }
  document.addEventListener('keydown', esc);
  mask.querySelector('#sheet-close').onclick = close;
  mask.onclick = ev => { if (ev.target === mask) close(); };
  mask.querySelector('#sheet-share').onclick = async () => {
    try {
      const file = new File([blob], filename, { type: 'image/png' });
      if (navigator.canShare && navigator.canShare({ files: [file] }) && navigator.share) {
        await navigator.share({ files: [file], title: '《后会友期》友情海报' });
      } else toast('此浏览器不支持图片分享，请长按上方海报保存');
    } catch (err) { if (err.name !== 'AbortError') toast('系统分享不可用，请长按上方图片保存'); }
  };
}
async function download() {
  if (!current) return;
  const b = $('#download');
  const label = b ? b.textContent : '';
  if (b) { b.disabled = true; b.textContent = '正在生成…'; }
  try {
    const im = await photoImg(current.id);
    const canvas = document.createElement('canvas');
    canvas.width = 1080; canvas.height = 1920;
    if (!qrLib) await ensureQR();
    drawPoster(canvas, current, im, selectedTemplate, !!qrLib);
    const blob = await new Promise((resolve, reject) => canvas.toBlob(v => v ? resolve(v) : reject(Error('png_export_failed')), 'image/png'));
    const filename = '后会友期-友情嘴替-' + current.name + '-' + selectedTemplate + '.png';
    if (mobileSaveMode()) {
      showPosterSaveSheet(blob, filename, canvas);
      toast('海报已生成，长按即可保存');
    } else {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = filename;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 8000);
      toast('已下载 1080×1920 海报');
    }
  } catch (err) {
    toast(err.message === 'png_export_failed' ? '海报生成失败，请重试' : '人物照片还没加载好，刷新后再试');
  } finally { if (b) { b.disabled = false; b.textContent = label; } }
}

/* ---------------- 启动 ---------------- */
async function init() {
  try {
    const t = localStorage.getItem('hhyq-template');
    if (templates.some(x => x.id === t)) selectedTemplate = t;
  } catch (err) { }
  try { portraitFocus = JSON.parse(localStorage.getItem('hhyq-focus') || '{}') || {}; } catch (err) { portraitFocus = {}; }
  await restorePhotos();
  const r = new URL(location.href).searchParams.get('r');
  if (r && C[r]) { current = C[r]; fromQuiz = false; renderResult(); }
  else home();
}
window.addEventListener('popstate', () => {
  const r = new URL(location.href).searchParams.get('r');
  if (r && C[r]) { current = C[r]; fromQuiz = false; renderResult(); } else home();
});
init();
