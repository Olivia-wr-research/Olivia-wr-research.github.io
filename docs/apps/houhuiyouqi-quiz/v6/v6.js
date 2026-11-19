'use strict';
/* 《后会友期》友情人物测试 V6
   非官方粉丝创作：情境来自公开节目片段，人物标签与文案为原创趣味类比。 */

const APP_PATH = 'https://olivia-wr-research.github.io/apps/houhuiyouqi-quiz/';
const MEDIA_ROOT = new URL('/apps/houhuiyouqi-quiz/v6/', location.origin).href;
const SHARE_PATH = MEDIA_ROOT + 'share/';
const thumbnailSrc = id => MEDIA_ROOT + 'photos-thumb/' + id + '.webp';
const screenPhotoSrc = id => customPhotos[id] || MEDIA_ROOT + 'photos-screen/' + id + '.webp';
const EPISODE = 'https://www.mgtv.com/h/914227.html';
const EVIDENCE = 'https://www.mgtv.com/act/2026/hhyq2026/';

const templates = [
  { id: 'cinema',  name: 'A / 公路电影', desc: '一张电影帧' },
  { id: 'ticket',  name: 'B / 友情车票', desc: '一张不退票' },
  { id: 'magazine',name: 'C / 人物特刊', desc: '一期封面' },
  { id: 'thread',  name: 'D / 评论区',   desc: '一条弹幕' }
];

const photoSources = {
  li:    { url: MEDIA_ROOT + 'photos-hd/li.webp', credit: '人物照片由站点维护者提供；据其说明来自官方平台发布，版权归原权利人。' },
  xu:    { url: MEDIA_ROOT + 'photos-hd/xu.webp', credit: '人物照片由站点维护者提供；据其说明来自官方平台发布，版权归原权利人。' },
  zhang: { url: MEDIA_ROOT + 'photos-hd/zhang.webp', credit: '人物照片由站点维护者提供；据其说明来自官方平台发布，版权归原权利人。' },
  ma:    { url: MEDIA_ROOT + 'photos-hd/ma.webp', credit: '人物照片由站点维护者提供；据其说明来自官方平台发布，版权归原权利人。' },
  wen:   { url: MEDIA_ROOT + 'photos-hd/wen.webp', credit: '人物照片由站点维护者提供；据其说明来自官方平台发布，版权归原权利人。' },
  wang:  { url: MEDIA_ROOT + 'photos-hd/wang.webp', credit: '人物照片由站点维护者提供；据其说明来自官方平台发布，版权归原权利人。' },
  qing:  { url: MEDIA_ROOT + 'photos-hd/qing.webp', credit: '人物照片由站点维护者提供；据其说明来自官方平台发布，版权归原权利人。' },
  bai:   { url: MEDIA_ROOT + 'photos-hd/bai.webp', credit: '人物照片由站点维护者提供；据其说明来自官方平台发布，版权归原权利人。' }
};

const characters = [
{id:'li',name:'厉娜',title:'友情「查完字典点麦当劳」派',stamp:'查完字典，我点了麦当劳',meme:'别人：TA 在你面前都哭了，你真没反应？\n你：我回房间查了一下“画地为牢”是什么意思。',caption:'表面：没什么好说的。\n心里：发生过的事，不会因为时间久就变成没发生。',touch:'你不是把旧事记成账本，而是知道有些伤口不能靠一句“算了吧”解决。你可以允许对方把话说完，也允许自己保留感受。对你来说，体面的告别和重新开始一样值得尊重。',weak:'太习惯自己消化情绪，别人可能不知道你真的有多难过。',mission:'你的友情通关提示：不必为了证明大度，把还没愈合的事轻轻带过。',scenetitle:'节目对应：厉娜与许飞车上对谈，以及“不一定继续做朋友”的表达',scenesrc:EVIDENCE,pair:'许飞',tags:['钝感但清醒','名字当句号','先查再答'],dims:[18,80,27,28,30],theme:'#748b95'},
{id:'xu',name:'许飞',title:'友情「我画地为牢」派',stamp:'我画地为牢，厉娜',meme:'别人：都过去十五年了，你还不走出来？\n你：我是被宣判的人，我能去哪儿？我画地为牢，厉娜。',caption:'嘴上：都过去了。\n脑内：那段友情的复盘文档已自动打开第18版。',touch:'你在意的不是赢一场争论，而是想知道两个人为什么从亲近走到了这里。你愿意翻开旧信，也愿意试着把没说完的话讲出来。但你慢慢会明白：表达你的版本很重要，接受对方未必给你同一种答案也很重要。',weak:'你有时候把“说清楚”误当成“还能回到从前”。',mission:'你的友情通关提示：说完想说的话，就已经完成了自己的那一部分。',scenetitle:'节目对应：许飞读介绍信落泪、与厉娜谈过往及询问能否重新做朋友',scenesrc:EVIDENCE,pair:'厉娜',tags:['画地为牢型','复盘十级学者','十五年未翻页'],dims:[85,35,81,37,70],theme:'#7b9b91'},
{id:'zhang',name:'张萌',title:'友情「删了微信也要送杯子」派',stamp:'备注删了，记得还在',meme:'别人：都断联了还买礼物？\n你：好友可以不在列表，但还在我的购物灵感里。',caption:'嘴上：没关系，不联系就算了。\n购物车：这杯子TA应该会喜欢。',touch:'你是那种看到一个小物件就会突然想到某个旧友的人。对你来说，关系不是一道非黑即白的选择题。你愿意主动靠近，也容易在热情里忘记：对方或许还没有准备好。你的勇敢很珍贵，尊重对方的节奏也很重要。',weak:'好意跑得比沟通快，偶尔会变成别人感受到的压力。',mission:'你的友情通关提示：送礼物之前，先确认对方愿不愿意重新打开那扇门。',scenetitle:'节目对应：张萌提到断联期间仍记得马天宇喜欢收藏马克杯',scenesrc:EPISODE,pair:'马天宇',tags:['纪念型人格','礼物派','热情先行'],dims:[82,35,68,78,62],theme:'#a8825f'},
{id:'ma',name:'马天宇',title:'友情「边界感保安队长」派',stamp:'不仅识字，还念给青稚听',meme:'别人：我们关系这么好，你还分什么边界？\n你：好朋友也得敲门，门禁不是装饰。',caption:'表面：我只想自己待会儿。\n真心：我很珍惜你，但我不能把所有空间都交出去。',touch:'你喜欢的是彼此尊重、允许各自独处的关系。对方太急于替你安排时，你会迅速感到疲惫。你不一定少情，也不一定冷淡；你只是更相信，长久的亲密应该留得下自由活动的空间。',weak:'你习惯用退后表示不舒服，别人可能根本没有收到通知。',mission:'你的友情通关提示：边界明确很酷，偶尔解释清楚会更省力。',scenetitle:'节目对应：马天宇谈享受独处，并就张萌的相处方式表达边界感',scenesrc:EVIDENCE,pair:'张萌',tags:['独处是刚需','越界提醒器','尊重双向选择'],dims:[28,91,38,27,30],theme:'#66808f'},
{id:'wen',name:'文吉儿',title:'友情「唯一好友单推人」派',stamp:'我不想做朋友了',meme:'别人：朋友又不是单选题。\n你：我知道啊，我只是想当那道压轴大题。',caption:'嘴上：你交新朋友没关系。\n心里：那我们的专属默契，还有没有名字？',touch:'你能接受朋友拥有自己的世界，却很在意某种只有彼此才懂的连接是否还存在。你会记住过去的承诺，也会敏锐地察觉关系的微小变化。你想要的并不是控制，而是一份被认真放在心上的确定感。',weak:'当亲密的定义不一样时，你可能把对方的自由误读成自己不够重要。',mission:'你的友情通关提示：与其猜自己是不是唯一，不如说出你真正想被怎样对待。',scenetitle:'节目对应：文吉儿与王子璇对好友“唯一性”的期待差异',scenesrc:EPISODE,pair:'王子璇',tags:['专属感','记得承诺','需要确定'],dims:[54,34,50,29,93],theme:'#a0726f'},
{id:'wang',name:'王子璇',title:'友情「好友列表非单选」派',stamp:'重要不用限量',meme:'别人：我是你唯一的朋友吗？\n你：你是重要的人，但我的通讯录不参加排他赛。',caption:'表面：大家都能好好相处。\n心里：为什么我交新朋友，也需要交一份解释报告？',touch:'你珍惜亲密，也看重相处中的选择空间。对你来说，友谊不是占有权证明，而是各自都能自然做自己。可当对方特别需要确定感时，你的轻松可能被听成疏远；你也需要学会把“重要”说得更具体。',weak:'过分相信“对方应该懂”，往往让沉默变成了误解。',mission:'你的友情通关提示：自由是底色，让对方感到被珍惜也并不矛盾。',scenetitle:'节目对应：王子璇与文吉儿围绕朋友关系及亲密期待的讨论',scenesrc:EPISODE,pair:'文吉儿',tags:['不排他','自在优先','直给沟通'],dims:[40,82,73,52,21],theme:'#7d9a86'},
{id:'qing',name:'青稚',title:'友情「雷王归位」派',stamp:'队可以掉线，人不能先走',meme:'别人：不是都散伙了吗，还这么上头？\n你：这队我还没放弃。',caption:'嘴上：各走各的也行。\n行动：但这队要是还能救，我还是会回头拉一把。',touch:'你很重视并肩作战积累出来的默契，所以当合作变了味，你往往比别人更难受。你可能嘴硬、可能急着争个结果，但心里其实还希望彼此能再次好好配合。有些关系不是不重要，而是你们还没学会用同一种速度沟通。',weak:'你太想立刻推进局面，反而可能让需要冷静的人更想后退。',mission:'你的友情通关提示：想重组一支队伍，第一步也许不是冲锋，而是听清对方想去哪。',scenetitle:'节目对应：青稚与白小纯在旅行中出现分歧、落泪与尝试重新同行',scenesrc:EVIDENCE,pair:'白小纯',tags:['雷王','不想散场','行动先行'],dims:[87,29,65,90,61],theme:'#6f8894'},
{id:'bai',name:'白小纯',title:'友情「先对线后搬行李」派',stamp:'明明是很好的陈礼根',meme:'别人：你俩不是吵架了吗？\n你：吵归吵，行李那么重，手也不能闲着啊。',caption:'表面：这件事我有我的观点。\n真心：但我也没说不在乎你。',touch:'你不是遇事会轻易低头的人，讲道理、保留立场对你很重要。可这不妨碍你在具体的事上伸手帮忙。你知道关系的复杂就在这里：情绪可以拧巴，行动里却仍然留着温度。',weak:'当你太在意把事情讲对，别人可能只听到了你的态度，没有看到你的关心。',mission:'你的友情通关提示：观点可以先放桌上，心意也值得被对方看见。',scenetitle:'节目对应：白小纯与青稚争执后仍帮忙搬行李、邀请回屋',scenesrc:EVIDENCE,pair:'青稚',tags:['行动派嘴替','不服软但会帮忙','理性在线'],dims:[44,65,88,79,34],theme:'#7f8f8a'}
];

const C = Object.fromEntries(characters.map(p => [p.id, p]));

const NICK = {li:'麦当劳点了', xu:'画地为牢本人', zhang:'马克杯保管员', ma:'郊区返乡人', wen:'唯一好友单推人', wang:'通讯录非单选', qing:'雷王', bai:'一本摊开的书'};

/* 真梗层：每条都对应节目公开片段或网友二创，不发明新梗 */
/* 首页卡片专用短梗：卡片窄，必须一行放得下 */
const CASTMEME = {
  li:'我点了麦当劳。', xu:'我画地为牢啊。', zhang:'好友不在列表也行。', ma:'人类好可怕。',
  wen:'我只想当压轴大题。', wang:'又不是单选题。', qing:'雷王还没退位。', bai:'道理讲完，行李得搬。'
};
const MEME2 = {
  li:  ['别人：TA 在你面前都哭了，你真没反应？', '你：我回房间查了一下“画地为牢”是什么意思。'],
  xu:  ['别人：都过去十五年了，你还不走出来？', '你：我是被宣判的人，我能去哪儿？我画地为牢，厉娜。'],
  zhang:['别人：都删微信了还送杯子？', '你：好友可以不在列表，杯子不能。'],
  ma:  ['别人：怎么不多交几个朋友？', '你：人类好可怕，我要回郊区了。'],
  wen: ['别人：朋友又不是只能有一个。', '你：那三万写序费，退我。'],
  wang:['别人：你朋友挺多的吧。', '你：朋友又不是单选题。'],
  qing:['别人：都散伙了还这么上头？', '你：这队我还没放弃。'],
  bai: ['别人：你俩不是刚吵完？', '你：道理讲完了，行李还得搬。']
};
const MEMES = {
  li: [
    ['许飞画地为牢，厉娜吃麦当劳','网友二创 · 悬崖对谈之后','一边是十五年的心结，一边是查完字典顺手点的一份套餐。'],
    ['XX 了，厉娜','网友二创 · 万能造句模板','任何一句日常碎碎念，加上“厉娜”两个字就有了怅然。她是全网最温柔的句号。'],
    ['不是不原谅，是不强制原谅','节目片段 · 车上对谈','把“原谅”从义务里摘出来：我可以不恨你，但也不必假装什么都没发生。']
  ],
  xu: [
    ['我画地为牢，厉娜','节目原话 · 高原悬崖对谈','“我是被宣判的人，我能去哪儿啊”——判决的人和服刑的人是同一个。'],
    ['我等这一刻等了十五年了，厉娜','节目原话 · 被剪成全网 BGM','十五年后再见，第一句不是责怪，是“我等这一刻”。'],
    ['老兵烧烤，今天出摊','节目片段 · 烧烤时把扇子转向','整晚扇子只朝自己这边扇。老兵没解释，他只是在做。']
  ],
  zhang:[
    ['马克杯保管员','节目片段 · 断联多年仍记得对方收藏马克杯','关系可以删掉，爱好删不掉——你喜欢什么，我还记得。'],
    ['好友可以不在列表，礼物不能缺席','网友二创','微信删了，购物车还留着。']
  ],
  ma: [
    ['人类好可怕，我要回郊区了','节目片段 · 密友数测出零','全场都在算谁朋友多，他算出来是零，然后给出了最诚实的反应。'],
    ['不仅识字，还大声念给青稚听','节目片段 · 当众念出那张心结卡','白小纯把心事写下来，他不但读了，还念给当事人听——摊开的书，遇上一个识字的人。'],
    ['马克杯收藏家 · 边界感保安队长','网友二创','一边收杯子，一边守门禁。']
  ],
  wen: [
    ['友情仅退款','网友二创 · 三万写序费','节目里的一个玩笑数字，被网友做成了电商短语——笑的是说法，不是人。'],
    ['我不想做朋友了','节目原话','不绕弯，不体面，直接说出口。']
  ],
  wang:[
    ['朋友又不是单选题','节目原话','把“唯一”这道题，直接改成多选。'],
    ['我的通讯录不参加排他赛','网友二创','扩写版：朋友可以有很多个，重要不需要限量。']
  ],
  qing:[
    ['雷王归位','荣誉墙 · 雷神杯冠军','奖杯摆在那儿，人也就没真正退过场。'],
    ['队可以掉线，人不能先走','节目片段 · 落泪后仍想重组','哭完第一句还是“能不能再组一次”。']
  ],
  bai: [
    ['白小纯是一本摊开的书，马天宇识字还念给青稚听','节目片段 · 当众念出那张心结卡','他什么都写在脸上，对方还没读，旁边的人先替他念了出来。'],
    ['明明是很好的陈礼根','网友二创 · 本名梗','本名叫陈礼根，人挺好的，只是梗盖过了名字。'],
    ['主打一个事事有回应，事事没着落','节目片段 · 狼人杀开麦当预言家','答应得很痛快，落地很随机。']
  ]
};
/* 只写节目里真实同框过的组合；第二名若不是固定搭档，就不显示关系卡 */
const PAIRS = {
  'li-xu':  '你早就走出那个圈了，TA 还站在原地喊你的名字。你查完字典点了份套餐，TA 的十五年还没翻页。',
  'xu-li':  '你把自己关在十五年前，TA 已经在圈外过日子。你喊她名字的时候，她正在查“画地为牢”是什么意思。',
  'zhang-ma':'你记得 TA 喜欢什么杯子，TA 记得的是一扇关着的门。礼物送得出去，边界送不进去。',
  'ma-zhang':'你需要敲门，TA 直接推门进来还带着礼物。你不讨厌那份心意，只是不喜欢没有门禁。',
  'wen-wang':'你想要一个“唯一”，TA 觉得“重要”不需要限量。三万块写序费退得回来，位置退不回来。',
  'wang-wen':'你觉得朋友不该是单选题，TA 把你的自由读成了“我不够重要”。',
  'qing-bai':'一个把训练当全部，一个把心事写在脸上。话都摊开了，就是没对上频。',
  'bai-qing':'你写“训练像坐牢”，TA 当众念了出来。吵归吵，行李还是你搬的。'
};
const HOTLINES = [['我画地为牢，厉娜','xu'],['我等这一刻等了十五年了','xu'],['查完字典点了麦当劳','li'],['人类好可怕，我要回郊区了','ma'],['白小纯是一本摊开的书','bai'],['雷王归位','qing'],['老兵烧烤出摊了','xu'],['明明是很好的陈礼根','bai'],['朋友又不是单选题','wang'],['我不想做朋友了','wen'],['马克杯还记得','zhang'],['训练像坐牢','bai'],['XX 了，厉娜','li'],['这队我还没散','qing']];

const Q = [
  {
    "scene": "01 / 久违的消息",
    "title": "曾经每天分享生活的朋友，已经半年没有联系。某天，TA突然发来一句：“看到这个，想起你了。”",
    "fact": "",
    "opts": [
      [
        "自然接话，像昨天才聊过天一样。",
        [
          2,
          -1,
          1,
          2,
          1
        ]
      ],
      [
        "先有点意外，想知道TA为什么突然想起我。",
        [
          0,
          0,
          0,
          -1,
          1
        ]
      ],
      [
        "很想说“其实我也想起过你”，但未必真的说出口。",
        [
          1,
          0,
          -2,
          -1,
          2
        ]
      ],
      [
        "认真回复，但不会因此期待关系回到从前。",
        [
          -1,
          2,
          1,
          -1,
          -1
        ]
      ]
    ]
  },
  {
    "scene": "02 / 不说出来的难过",
    "title": "朋友最近明显状态不好，却只说：“没什么，我想一个人待会儿。”你更可能？",
    "fact": "",
    "opts": [
      [
        "尊重TA的空间，过几天再轻轻问候。",
        [
          0,
          2,
          0,
          -1,
          -1
        ]
      ],
      [
        "不追问，安静陪TA走一段路。",
        [
          1,
          0,
          -1,
          1,
          1
        ]
      ],
      [
        "留意TA最近有什么实际困难，能帮就帮。",
        [
          1,
          0,
          -1,
          2,
          0
        ]
      ],
      [
        "直接告诉TA：“你想说的时候，我愿意听。”",
        [
          2,
          0,
          2,
          1,
          0
        ]
      ]
    ]
  },
  {
    "scene": "03 / 只剩表情包",
    "title": "你和一位朋友曾经无话不谈。现在，你们只会偶尔互发一些无聊的视频和表情包。你的感受更接近？",
    "fact": "",
    "opts": [
      [
        "这样也很好。看到好笑的东西还会想起对方，本身就很珍贵。",
        [
          0,
          0,
          0,
          0,
          1
        ]
      ],
      [
        "有点想念以前能认真聊到深夜的日子。",
        [
          1,
          -1,
          -1,
          -1,
          2
        ]
      ],
      [
        "人总会变，找到新的相处节奏也挺好。",
        [
          -1,
          2,
          0,
          -1,
          -1
        ]
      ],
      [
        "如果可以，我还是想找个机会重新聊聊彼此的生活。",
        [
          2,
          0,
          2,
          2,
          1
        ]
      ]
    ]
  },
  {
    "scene": "04 / 不再只有我们",
    "title": "你最亲近的朋友有了新的朋友圈。TA依然对你很好，但你们不再分享所有事情。你的真实反应是？",
    "fact": "",
    "opts": [
      [
        "好奇TA的新生活，也愿意听TA讲那些我不认识的人。",
        [
          1,
          0,
          1,
          1,
          -2
        ]
      ],
      [
        "偶尔失落，怀念只有我们才懂的默契。",
        [
          0,
          -1,
          -1,
          -1,
          2
        ]
      ],
      [
        "觉得正常，亲密不等于要参与彼此生活的全部。",
        [
          -1,
          2,
          0,
          0,
          -2
        ]
      ],
      [
        "想约TA单独见面，找回只属于我们的相处时间。",
        [
          2,
          -1,
          2,
          2,
          2
        ]
      ]
    ]
  },
  {
    "scene": "05 / 不同的选择",
    "title": "一位重要的朋友做了一个你不太认同、但对TA意义重大的决定。你会？",
    "fact": "",
    "opts": [
      [
        "先听TA为什么这样选择，再谈自己的看法。",
        [
          1,
          0,
          1,
          0,
          0
        ]
      ],
      [
        "认真说出我的担忧，即使TA可能不爱听。",
        [
          1,
          1,
          2,
          1,
          0
        ]
      ],
      [
        "不急着评价，先帮TA想好遇到困难时怎么办。",
        [
          2,
          0,
          0,
          2,
          0
        ]
      ],
      [
        "保留不同意见，相信TA有权为自己的选择负责。",
        [
          -1,
          2,
          0,
          -1,
          -1
        ]
      ]
    ]
  },
  {
    "scene": "06 / 无意的玩笑",
    "title": "朋友随口开了个玩笑。TA可能觉得无伤大雅，你却真的有些难过。你会？",
    "fact": "",
    "opts": [
      [
        "用玩笑提醒TA：“这个梗下次别用了。”",
        [
          1,
          1,
          1,
          1,
          0
        ]
      ],
      [
        "先想想自己为什么这么在意这句话。",
        [
          0,
          0,
          -2,
          -1,
          0
        ]
      ],
      [
        "找个合适的机会认真告诉TA，这件事让我不舒服。",
        [
          1,
          1,
          2,
          0,
          0
        ]
      ],
      [
        "暂时不提，但会留意类似情况是否再次发生。",
        [
          -1,
          2,
          -1,
          -1,
          0
        ]
      ]
    ]
  },
  {
    "scene": "07 / 总是我先联系",
    "title": "这半年，几乎每一次见面都是你主动约。TA每次都愿意来，却很少主动联系。你会？",
    "fact": "",
    "opts": [
      [
        "找机会问问，最近我们是不是有什么变化。",
        [
          2,
          0,
          2,
          0,
          1
        ]
      ],
      [
        "不再计算谁先找谁，想见的时候还是会联系。",
        [
          2,
          -1,
          1,
          2,
          1
        ]
      ],
      [
        "调整期待，把更多时间留给其他关系和自己的生活。",
        [
          -1,
          2,
          0,
          1,
          -1
        ]
      ],
      [
        "暂时停止主动，看看这段关系会不会自己向前走一步。",
        [
          -1,
          1,
          -1,
          -1,
          1
        ]
      ]
    ]
  },
  {
    "scene": "08 / 两种记忆",
    "title": "和朋友聊起一件多年前共同经历的事，你发现TA记得的细节，甚至当时的感受，都与你完全不同。你会？",
    "fact": "",
    "opts": [
      [
        "认真讲出我的版本，希望TA知道那时我是怎样想的。",
        [
          1,
          0,
          2,
          0,
          1
        ]
      ],
      [
        "想弄明白，为什么同一件事会在我们心里留下不同痕迹。",
        [
          2,
          0,
          2,
          1,
          1
        ]
      ],
      [
        "接受彼此有不同的记忆，不一定非要分出谁对谁错。",
        [
          0,
          2,
          -1,
          0,
          -1
        ]
      ],
      [
        "不再纠结过去，希望以后能创造新的共同回忆。",
        [
          2,
          -1,
          0,
          2,
          0
        ]
      ]
    ]
  },
  {
    "scene": "09 / 总没成行的见面",
    "title": "你和一位重要朋友生活在不同城市。你们好几次说要见面，却总因为各自的安排没有成行。你更倾向于？",
    "fact": "",
    "opts": [
      [
        "主动定一个具体日期，想见就努力把它变成现实。",
        [
          2,
          -1,
          1,
          2,
          1
        ]
      ],
      [
        "不一定非要见面，日常保持一点联系也能维系感情。",
        [
          1,
          1,
          0,
          0,
          0
        ]
      ],
      [
        "接受人生阶段不同，不再要求关系维持原来的频率。",
        [
          -2,
          2,
          -1,
          -1,
          -2
        ]
      ],
      [
        "坦白告诉TA：“其实一直没见成，我真的有点失落。”",
        [
          1,
          0,
          2,
          0,
          2
        ]
      ]
    ]
  },
  {
    "scene": "10 / 如果回不到从前",
    "title": "假如有一天，你清楚地知道，一段曾经很重要的友情再也无法回到过去。你最希望留下的是？",
    "fact": "",
    "opts": [
      [
        "一种轻松的联系。以后偶尔说说近况，依然能自然地笑。",
        [
          1,
          1,
          1,
          1,
          0
        ]
      ],
      [
        "一次真正坦诚的对话。那些没说出口的话，至少有机会被听见。",
        [
          2,
          0,
          2,
          0,
          1
        ]
      ],
      [
        "一份相互尊重。不再同行，也不必否定对方曾经的重要。",
        [
          -2,
          2,
          0,
          -1,
          -1
        ]
      ],
      [
        "一个重新开始的可能。不复制过去，而是尝试建立新的关系。",
        [
          2,
          0,
          0,
          2,
          1
        ]
      ]
    ]
  }
];
const choiceAnchors = {"li":[3,0,2,2,3,3,2,2,2,2],"xu":[2,3,1,1,1,2,0,1,3,1],"zhang":[0,2,3,0,2,0,1,3,0,3],"ma":[3,0,2,2,3,0,2,2,1,0],"wen":[2,1,1,1,0,1,3,0,3,1],"wang":[0,0,2,0,3,0,2,2,1,0],"qing":[0,2,3,3,2,0,1,3,0,3],"bai":[1,2,0,2,1,2,0,0,0,1]};
const answerInsights = [["你愿意自然接住久违的联系，不急着计算时间。","你对意外的靠近保持好奇，也会先确认对方的心意。","你会想念，却未必急着把想念说出口。","你愿意认真回应，但不把一次消息当成重启的承诺。"],["你尊重对方独处的需要，也愿意保留轻柔的关心。","你习惯把关心放在不打扰的陪伴里。","你会用具体行动分担压力，而不是只追问情绪。","你愿意明确地告诉朋友：需要时我在。"],["你认可低频但轻松的联系，也是一种稳定关系。","你会怀念那些更深入的谈话和共同生活。","你允许一段关系随着人生阶段自然变形。","你会主动尝试重新建立深入的连接。"],["你对朋友的新生活保持好奇，不要求自己事事参与。","你珍惜两人间的独特记忆，也会感到失落。","你能够同时尊重亲密与彼此独立。","你会为重要的两人空间主动创造机会。"],["你倾向先理解对方的理由，再表达自己的意见。","你重视坦诚，即使真话不一定让双方舒服。","你更喜欢提供实际帮助，让关心落地。","你尊重朋友作为独立个体的选择权。"],["你愿意用轻松方式提醒边界，而不立即升级冲突。","你习惯先整理自己的感受，弄清难过从何而来。","你相信重要的感受值得被认真听见。","你会先观察这是否是偶发的误会，再决定如何行动。"],["你会主动确认关系是否发生变化，而不是长时间猜测。","你愿意发起联系，也不愿让主动变成算账。","你愿意为自己的生活重新分配时间与精力。","你会通过暂时后退，观察一段关系的双向性。"],["你希望自己的经历与感受被朋友真正理解。","你会认真探索双方为何形成不同的记忆。","你可以接受一件事存在不止一种叙述。","你更倾向把重心放在接下来一起创造什么。"],["你会把“有空再说”变成一个可以执行的计划。","你相信日常的小联系也能够维系关系。","你允许亲密程度随着生活阶段发生变化。","你会直接表达因为错过见面而产生的失落。"],["你希望友谊留下自然、轻松的联系。","你希望重要的话得到一个被听见的机会。","你认可珍贵不一定意味着必须继续同行。","你愿意用新的方式开始，而不执着于复制从前。"]];

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
function castStrip() {
  return '<div class="cast">' + characters.map((c, i) => {
    const url = e(thumbnailSrc(c.id));
    const attr = i < 4
      ? 'src="' + url + '" loading="eager" fetchpriority="' + (i === 0 ? 'high' : 'low') + '"'
      : 'data-src="' + url + '" loading="lazy" fetchpriority="low"';
    return '<figure data-person="' + c.id + '"><img ' + attr + ' alt="' + e(c.name) + '" decoding="async" width="360" height="540" data-hhyq-photo="' + c.id + '"><figcaption><span class="cast-name">' + e(c.name) + '</span><span class="cast-meme">' + e(CASTMEME[c.id] || '') + '</span></figcaption></figure>';
  }).join('') + '</div>';
}
let castObserver = null;
let castWindowScrollHandler = null;
let castWindowResizeHandler = null;
function loadCastImages(strip) {
  if (castObserver) { castObserver.disconnect(); castObserver = null; }
  if (castWindowScrollHandler) {
    window.removeEventListener('scroll', castWindowScrollHandler);
    castWindowScrollHandler = null;
  }
  if (castWindowResizeHandler) {
    window.removeEventListener('resize', castWindowResizeHandler);
    castWindowResizeHandler = null;
  }
  const pictures = [...strip.querySelectorAll('img[data-hhyq-photo]')];
  const originalQueue = [];
  let activeLoads = 0;

  const promoteOriginals = () => {
    while (activeLoads < 2 && originalQueue.length) {
      const img = originalQueue.shift();
      if (!img.isConnected || !strip.isConnected) continue;
      const id = img.dataset.hhyqPhoto;
      const full = new Image();
      activeLoads++;
      full.decoding = 'async';
      full.onload = () => {
        if (img.isConnected && strip.isConnected && img.dataset.hhyqPhoto === id) {
          // Never replace a visible thumbnail until the actual HD photo is downloaded.
          img.src = full.src;
          img.dataset.hdReady = '1';
          img.classList.remove('photo-unavailable');
        }
        activeLoads--;
        promoteOriginals();
      };
      full.onerror = () => {
        // Prefer a real full-resolution portrait JPEG over a text-covered share card.
        const jpeg = new Image();
        jpeg.decoding = 'async';
        jpeg.onload = () => {
          if (img.isConnected && strip.isConnected && img.dataset.hhyqPhoto === id) {
            img.src = jpeg.src;
            img.dataset.hdReady = 'jpeg';
            img.classList.remove('photo-unavailable');
          }
          activeLoads--;
          promoteOriginals();
        };
        jpeg.onerror = () => {
          img.dataset.hdFailed = '1'; // Retain the visible preview if both full-size sources fail.
          activeLoads--;
          promoteOriginals();
        };
        jpeg.src = MEDIA_ROOT + 'photos-hd-jpeg/' + id + '.jpg';
      };
      full.src = photoSources[id].url;
    }
  };
  const nearby = () => {
    if (!strip.isConnected) return;
    const r = strip.getBoundingClientRect();
    const verticallyNear = r.top < window.innerHeight + 100 && r.bottom > -100;
    for (const img of pictures) {
      const p = img.getBoundingClientRect();
      const withinLoadRange = p.left <= r.right + 240 && p.right >= r.left - 240;
      if (withinLoadRange && img.dataset.src) {
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
        if (castObserver) castObserver.unobserve(img);
      }
      if (verticallyNear && p.left <= r.right + 40 && p.right >= r.left - 40 &&
          img.src && !img.dataset.hdQueued && !img.dataset.hdReady) {
        img.dataset.hdQueued = '1';
        originalQueue.push(img);
      }
    }
    promoteOriginals();
  };
  if ('IntersectionObserver' in window) {
    castObserver = new IntersectionObserver(nearby, {root: strip, rootMargin: '0px 240px'});
    for (const img of pictures) if (img.dataset.src) castObserver.observe(img);
  }
  strip.addEventListener('scroll', nearby, {passive: true});
  castWindowScrollHandler = nearby;
  window.addEventListener('scroll', castWindowScrollHandler, {passive: true});
  castWindowResizeHandler = nearby;
  window.addEventListener('resize', castWindowResizeHandler, {passive: true});
  // The light previews and interactive title appear first; originals load afterward.
  nearby();
  if ('requestIdleCallback' in window) requestIdleCallback(nearby, {timeout: 250});
  else setTimeout(nearby, 100);
}
function heatStrip() {
  const items = ['前两期正片均破 1.4 亿播放', '连续 8 天登顶', '有效播放市占率 75.1%'].concat(HOTLINES.map(x => x[0]));
  const one = items.map(t => '<span class="hstrip-item">' + e(t) + '</span>').join('');
  return '<div class="hstrip" aria-hidden="true"><div class="hstrip-track">' + one + one + '</div></div>';
}
function home() {
  document.title = '谁是你的友情嘴替？｜后会友期 · 友情人物测试';
  document.body.classList.remove('has-bar');
  window.scrollTo(0, 0);
  app.innerHTML =
    '<main class="home">' + nav(true) + heatStrip() +
      '<div class="hero">' +
        '<div class="hero-copy">' +
          '<div class="kicker">Friendship / 友情售后中心</div>' +
          '<h1><span>旧友重逢，</span><span>谁是你的</span><span><em>互联网嘴替？</em></span></h1>' +
          '<p class="lead">有些关系不再像从前，却依然留在心里。<br>10 次友情选择，看看你在亲近、边界与告别之间，更像谁。</p>' +
          '<div class="meta"><span>10 题</span><span>约 3 分钟</span><span>8 位原型</span><span>4 款海报</span></div>' +
          '<div class="cta-row">' +
            '<button class="btn" id="start">开始测试 →</button>' +
          '</div>' +
          '<p class="legal">没有标准答案。别选最正确的，选更接近真实自己的。此为非官方趣味测试，不代表嘉宾真实人格或科学心理测量。</p>' +
        '</div>' +
        '<div class="hero-cast">' + castStrip() +
          '<div class="cast-note"><span>八位嘉宾 · 八种友情立场</span><span>SCROLL →</span></div>' +
        '</div>' +
      '</div>' +
    '</main>';
  const strip = $('.cast');
  if (strip) { strip.scrollLeft = 0; loadCastImages(strip); }
  $('#start').onclick = reset;
  app.querySelectorAll('[data-person]').forEach(el => {
    el.onclick = () => openCastSheet(characters.find(x => x.id === el.dataset.person));
  });
}

/* 首页：点开幕后，看这个人最出圈的那一句 */
function openCastSheet(p) {
  if (!p) return;
  let sheet = document.getElementById('msheet');
  if (!sheet) {
    sheet = document.createElement('div');
    sheet.id = 'msheet';
    sheet.className = 'msheet';
    sheet.innerHTML = '<div class="msheet-in"><div class="msheet-tag"></div>' +
      '<p class="msheet-q"></p><p class="msheet-src"></p><p class="msheet-why"></p>' +
      '<button class="btn btn--ghost btn--sm" id="mclose">知道了</button></div>';
    document.body.appendChild(sheet);
  }
  const top = (MEMES[p.id] || [])[0] || ['', ''];
  sheet.querySelector('.msheet-tag').textContent = p.name + ' · 最出圈的那一句';
  sheet.querySelector('.msheet-q').textContent = '「' + top[0] + '」';
  sheet.querySelector('.msheet-src').textContent = top[1] || '';
  sheet.querySelector('.msheet-why').textContent = top[2] || '';
  sheet.classList.add('on');
  const close = () => sheet.classList.remove('on');
  sheet.querySelector('#mclose').onclick = close;
  sheet.onclick = ev => { if (ev.target === sheet) close(); };
}

/* ---------------- 答题 ---------------- */
function reset() {
  step = 0; answers = Array(Q.length).fill(-1); fromQuiz = false;
  selectedTemplate = 'cinema';
  try { sessionStorage.removeItem('hhyq-progress'); } catch (err) { }
  history.replaceState({}, '', location.pathname);
  renderQuestion();
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
            '</div>' +
          '<div class="opts"><div class="opts-inner">' +
            q.opts.map((o, i) =>
              '<button class="opt" data-ans="' + i + '" aria-pressed="' + (answers[step] === i) + '">' +
                '<span class="opt-key">' + ('ABCD'[i]) + '</span><span class="opt-text">' + e(o[0]) + '</span></button>').join('') +
          '</div></div>' +
        '</section>' +
        '<div class="qfoot"><button class="qback" id="back">' + (step ? '← 上一站' : '← 回首页') + '</button>' +
          '<span class="qhint">选完<b>自动</b>进入下一站</span></div>' +
        '<p class="qhint">没有标准答案；请按自己真实的反应作答。</p>' +
      '</div>' +
    '</main>';

  document.querySelectorAll('[data-ans]').forEach(b => b.onclick = () => choose(Number(b.dataset.ans)));
  $('#back').onclick = () => { if (step === 0) home(); else { step--; renderQuestion(); } };
  document.onkeydown = onKey;
}

function choose(i) {
  if (advancing) return;
  answers[step] = i;
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
    history.replaceState({}, '', location.pathname);
    renderResult();
  } else { step++; renderQuestion(); }
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
function scoreDistanceFor(c, a) {
  const v = scoreForTests(a);
  const dimensions = c.dims.reduce((sum, x, k) => sum + (x - v[k]) ** 2 * (k === 4 ? 1.12 : 1), 0) / 50000;
  const choices = a.reduce((sum, choice, i) => sum + (choice !== choiceAnchors[c.id][i] ? 1 : 0), 0) / Q.length;
  return .4 * choices + .6 * dimensions;
}
function scoreResult() {
  const ranking = characters.map(c => ({ c, dist: scoreDistanceFor(c, answers) }))
    .sort((a, b) => a.dist - b.dist || characters.indexOf(a.c) - characters.indexOf(b.c));
  ranking[0].c.runner = ranking[1].c.name;
  ranking[0].c.runnerId = ranking[1].c.id;
  ranking[0].c.match = Math.max(38, Math.min(96, Math.round(100 - ranking[0].dist * 74)));
  return ranking[0].c;
}
function evidenceBlock(c) {
  const real = fromQuiz && answers.every(a => Number.isInteger(a) && a >= 0 && a < 4) && scoreResult().id === c.id;
  if (!real) {
    return '<p class="note">这里是可分享的人物画像。自己答完10道题后，才能看到你的专属选项线索；分享链接不携带私人答案。</p>';
  }
  const runner = characters.find(p => p.name === c.runner);
  if (!runner) return '<p class="note">你已完成10道题，以下人物画像由固定的游戏规则匹配，不代表心理学鉴定。</p>';
  const picks = answers.map((choice, i) => {
    // Difference in the winner-vs-runner margin caused by this answer, compared with all four possible options.
    const hypothetical = [0, 1, 2, 3].map(option => {
      const a = answers.slice(); a[i] = option;
      return scoreDistanceFor(runner, a) - scoreDistanceFor(c, a);
    });
    const average = hypothetical.reduce((sum, n) => sum + n, 0) / 4;
    return { i, delta: hypothetical[choice] - average, text: answerInsights[i][choice] };
  });
  const supporting = picks.filter(p => p.delta > 1e-7).sort((a, b) => b.delta - a.delta || a.i - b.i);
  const alternative = picks.filter(p => p.delta < -1e-7).sort((a, b) => a.delta - b.delta || a.i - b.i);
  const chosen = supporting.slice(0, 3);
  if (alternative.length && (chosen.length < 3 || -alternative[0].delta > chosen[2].delta * 1.12)) {
    if (chosen.length === 3) chosen.pop();
    chosen.push(alternative[0]);
  }
  for (const p of [...supporting, ...alternative, ...picks]) {
    if (chosen.length >= 3) break;
    if (!chosen.some(x => x.i === p.i)) chosen.push(p);
  }
  chosen.sort((a, b) => a.i - b.i);
  return '<div class="evidence">' + chosen.map(p => {
    const relation = p.delta > 1e-7 ? '更接近 ' + c.name + ' 型' :
      (p.delta < -1e-7 ? '也有点像 ' + runner.name + ' 型' : '两种人设都可能这样选');
    return '<div class="ev"><span>第' + (p.i + 1) + '题 · ' + e(relation) + '</span><p>' + e(p.text) + '</p></div>';
  }).join('') + '</div>' +
    '<p class="note">线索依据本次选项对第一名与第二名游戏分数差距的影响筛选；存在“另一面”是正常的。仅是娱乐规则，不是人格测评。</p>';
}

/* ---------------- 照片 ---------------- */
function getPhotoSrc(id) { return customPhotos[id] || (photoSources[id] && photoSources[id].url) || ''; }
const defaultFocus = { li: 40, xu: 38, zhang: 42, ma: 24, wen: 38, wang: 38, qing: 36, bai: 42 };
function getFocus(id) { return Math.min(95, Math.max(5, Number(portraitFocus[id] ?? defaultFocus[id] ?? 40))); }
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
    im.onerror = () => {
      if (!im.dataset.posterFallback) {
        im.dataset.posterFallback = 'jpeg';
        im.src = MEDIA_ROOT + 'photos-hd-jpeg/' + id + '.jpg';
      } else if (im.dataset.posterFallback === 'jpeg') {
        im.dataset.posterFallback = 'cover';
        im.src = MEDIA_ROOT + 'share-cover-' + id + '.jpg';
      } else finish(null);
    };
    const timer = setTimeout(() => finish(null), 18000);
    im.src = src;
  });
  imgCache[id] = { src, promise };
  promise.then(img => { if (!img && imgCache[id] && imgCache[id].src === src) delete imgCache[id]; });
  return promise;
}

/* ---------------- 结果 ---------------- */
function openMemeSheet(c, m) {
  if (!m) return;
  let sheet = document.getElementById('msheet');
  if (!sheet) {
    sheet = document.createElement('div');
    sheet.id = 'msheet';
    sheet.className = 'msheet';
    sheet.innerHTML = '<div class="msheet-in"><div class="msheet-tag">这句梗的出处</div>' +
      '<p class="msheet-q"></p><p class="msheet-src"></p><p class="msheet-why"></p>' +
      '<button class="btn btn--ghost btn--sm" id="mclose">知道了</button></div>';
    document.body.appendChild(sheet);
  }
  sheet.querySelector('.msheet-q').textContent = '「' + m[0] + '」';
  sheet.querySelector('.msheet-src').textContent = m[1];
  sheet.querySelector('.msheet-why').textContent = m[2] || '';
  sheet.classList.add('on');
  const close = () => sheet.classList.remove('on');
  sheet.querySelector('#mclose').onclick = close;
  sheet.onclick = ev => { if (ev.target === sheet) close(); };
}
function pairLine(c) {
  const rid = c.runnerId || '';
  const hit = PAIRS[c.id + '-' + rid];
  if (hit) return hit;
  const other = characters.find(p => p.id === rid);
  if (!other) return '';
  // 不是节目固定搭档时，不编造关系，只做两组人设的正面对撞
  return '你的「' + c.tags[0] + '」撞上 TA 的「' + other.tags[0] + '」——同一件事，你们用的是两套语法。';
}
function resultHTML(c) {
  const meme = MEME2[c.id] || c.meme.split('\n');
  const caption = c.caption.split('\n');
  const k = s => s.split('：')[0];
  const v = s => s.split('：').slice(1).join('：');
  return '<main class="result">' + nav(false) +
    '<section class="verdict"><div class="verdict-inner">' +
      '<div class="verdict-head">' +
        '<div class="verdict-eyebrow">Result / 友情嘴替鉴定书</div>' +
        '<h1>' + e(c.name) + '<small>型</small></h1>' +
        '<div class="vtype">' + e(c.title) + '</div>' +
        (fromQuiz ? '<div class="vmatch"><b>' + (c.match || 0) + '</b><span>% 匹配度</span></div>' : '') +
        '<div class="valias"># 网友外号 · ' + e(NICK[c.id] || '') + '</div>' +
        '<span class="stamp">' + e(c.stamp) + '</span>' +
      '</div>' +
      '<figure class="portrait">' +
        '<div class="portrait-frame"><img id="portrait-img" src="' + e(screenPhotoSrc(c.id)) + '" alt="' + e(c.name) + ' 人物照片" data-hhyq-photo="' + c.id + '" style="object-position:center ' + getFocus(c.id) + '%"></div>' +
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
          '<button class="btn btn--ghost btn--sm" id="restart">再测一次</button></div>' +
      '</section>' +

      '<section class="sec"><div class="sec-label">07 <b>全网都在刷的梗</b></div>' +
        '<div class="memewall">' +
          (MEMES[c.id] || []).map((m, i) => '<button class="mcard" data-meme="' + i + '"><p class="mcard-q">「' + e(m[0]) + '」</p><p class="mcard-src">' + e(m[1]) + '</p><span class="mcard-more">点开看出处 →</span></button>').join('') +
        '</div>' +
        '<p class="memetip">↑ 点任意一张，看这句梗到底从哪来</p>' +
        (pairLine(c) ? '<div class="duocard"><b>你们这对 · ' + e(c.runner || '') + '</b><p>' + e(pairLine(c)) + '</p></div>' : '') +
        '<p class="mnote">以上为网友二创与节目公开片段的趣味改写，不是嘉宾本人发言，也不构成对真实性格的判断。</p>' +
      '</section>' +
    '</div>' +

    '<section class="poster" id="poster-chooser"><div class="poster-inner">' +
      '<h2>挑一张你愿意发出去的海报</h2>' +
      '<p class="sub">四款是不同的版式，不是换色。点一下就能预览，选好后保存成 1080×1920 的图片。</p>' +
      '<div class="tmpl-grid">' + templates.map(t =>
        '<button class="tmpl" data-template="' + t.id + '" aria-pressed="' + (t.id === selectedTemplate) + '">' +
          '<canvas id="canvas-' + t.id + '" width="720" height="1280" aria-label="' + e(t.name) + ' 海报预览"></canvas>' +
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
  const tline = (MEME2[current.id] || [''])[1] || current.stamp;
  document.title = '我是' + current.name + '型：' + current.stamp + '｜后会友期';
  document.body.classList.add('has-bar');
  window.scrollTo(0, 0);
  app.innerHTML = resultHTML(current);

  const toPoster = () => document.getElementById('poster-chooser').scrollIntoView({ behavior: 'smooth', block: 'start' });
  $('#go-poster').onclick = toPoster;
  $('#poster-cta').onclick = toPoster;
  $('#bar-poster').onclick = () => download();
  $('#share-link').onclick = share;
  $('#bar-share').onclick = share;
  $('#restart').onclick = reset;
  app.querySelectorAll('.mcard').forEach(el => {
    el.onclick = () => openMemeSheet(current, MEMES[current.id][+el.dataset.meme]);
  });
  $('#download').onclick = download;
  $('#copy-caption').onclick = copyCaption;
  $('#upload-button').onclick = () => $('#photo-upload').click();
  $('#edit-photo').onclick = () => { const t = $('.tune'); if (t) { t.open = true; t.scrollIntoView({ behavior: 'smooth', block: 'center' }); } $('#photo-upload').click(); };
  $('#photo-upload').onchange = handleUpload;

  document.querySelectorAll('[data-template]').forEach(x => x.onclick = () => {
    selectedTemplate = x.dataset.template;
    document.querySelectorAll('[data-template]').forEach(y => y.setAttribute('aria-pressed', String(y === x)));
    toast('已选中' + templates.find(t => t.id === selectedTemplate).name);
  });
  $('#character-preview').onchange = ev => {
    current = C[ev.target.value]; fromQuiz = false;
    history.replaceState({}, '', location.pathname);
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
  // Show a screen-size preview immediately, then replace it with the original HD photo.
  const shown = $('#portrait-img'), personId = current.id;
  if (shown && !customPhotos[personId] && credit) {
    const hd = new Image();
    hd.decoding = 'async';
    hd.onload = () => {
      if (shown.isConnected && current && current.id === personId && !customPhotos[personId]) {
        shown.src = credit.url;
        shown.dataset.hdReady = '1';
        shown.classList.remove('photo-unavailable');
      }
    };
    hd.onerror = () => {
      const jpeg = new Image();
      jpeg.onload = () => {
        if (shown.isConnected && current && current.id === personId && !customPhotos[personId]) {
          shown.src = jpeg.src;
          shown.dataset.hdReady = 'jpeg';
          shown.classList.remove('photo-unavailable');
        }
      };
      jpeg.src = MEDIA_ROOT + 'photos-hd-jpeg/' + personId + '.jpg';
    };
    hd.src = credit.url;
  }
  schedulePosterPreviews();
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
    current.stamp + '\n不是我对号入座，是这档节目在我心里装监控了。\n你测出谁？ ' + SHARE_PATH + current.id + '.html')
    .then(() => toast('朋友圈文案已复制'));
}
async function share() {
  if (isWeChat()) { copyCaption(); return; }
  const text = '我测出了《后会友期》友情嘴替：' + current.title + '。你也来测测！';
  const url = SHARE_PATH + current.id + '.html';
  try {
    if (navigator.share) await navigator.share({ title: '我是' + current.name + '型：' + current.stamp, text, url });
    else { await copyText(text + '\n' + url); toast('结果链接已复制'); }
  } catch (err) {
    if (err.name !== 'AbortError') { await copyText(text + '\n' + url); toast('结果链接已复制'); }
  }
}

function dbOpen() {
  return new Promise((resolve, reject) => {
    if (!window.indexedDB) return reject(Error('No DB'));
    const r = indexedDB.open('hhyq-v6-hd-custom-photos', 1);
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
    s.src = new URL('/apps/houhuiyouqi-quiz/qrcode.js', location.origin).href; s.async = true;
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

/* 票根备注：每人固定一句，已手工避开“印章”和“派别名”，三处不重复 */
const REMARK = {
  li:    '有些话，我还没想好怎么回',
  xu:    '我等这一刻，等了十五年',
  zhang: '马克杯保管员',
  ma:    '人类好可怕，我要回郊区了',
  wen:   '我想当那道压轴大题',
  wang:  '我的通讯录不参加排他赛',
  qing:  '雷王 · 雷神杯那位',
  bai:   '我是一本摊开的书，马天宇识字还念了出来'
};
function remarkOf(c) { return REMARK[c.id] || c.stamp; }
function drawPoster(cvs, c, img, t, qrReady) {
  const ctx = cvs.getContext('2d');
  const W = 900, H = 1600;
  ctx.setTransform(cvs.width / W, 0, 0, cvs.height / H, 0, 0);
  ctx.clearRect(0, 0, W, H);
  const focus = getFocus(c.id);

  if (t === 'cinema') {
    /* 一张电影帧：照片满版，字压在影像上 */
    ctx.fillStyle = NIGHT; ctx.fillRect(0, 0, W, H);
    if (img) cover(ctx, img, 0, 0, W, H, Math.max(12, focus - 6)); else artFallback(ctx, 0, 0, W, H, c);
    scrim(ctx, 0, H * .40, W, H * .60, 'rgba(6,18,26,0)', 'rgba(6,18,26,.96)');
    const headerShade = ctx.createLinearGradient(0, 0, 0, 320);
    headerShade.addColorStop(0, 'rgba(6,18,26,.60)');
    headerShade.addColorStop(.62, 'rgba(6,18,26,.20)');
    headerShade.addColorStop(1, 'rgba(6,18,26,0)');
    ctx.fillStyle = headerShade; ctx.fillRect(0, 0, W, 320);

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
    /* 备注栏：车票上那句手写体梗 */
    ctx.strokeStyle = 'rgba(18,36,47,.18)'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(84, 1440); ctx.lineTo(W - 320, 1440); ctx.stroke();
    spaced(ctx, '备注 / REMARK', 84, 1468, 12, '#A88355', 2, FMONO);
    const rk = remarkOf(c);
    font(ctx, 26, FSERIF);
    let rfs = 26;
    while (rfs > 15 && ctx.measureText('「' + rk + '」').width > W - 404) { rfs -= 1; font(ctx, rfs, FSERIF); }
    ctx.fillStyle = INK;
    ctx.fillText('「' + rk + '」', 84, 1494);
    if (qrReady) {
      drawQR(ctx, APP_PATH, W - 268, 1292, 168, INK, PAPER);
      spaced(ctx, '扫码测你的嘴替', W - 268, 1486, 13, DUST, 0, FSANS);
    }
    spaced(ctx, '非官方粉丝创作 · 票据仅供收藏', 84, 1532, 11, '#96907F', 0, FSANS);
    if (img) spaced(ctx, '人物照片由网站维护者提供', W - 300, 1532, 10, '#96907F', 0, FSANS);
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
    spaced(ctx, '想象中的友情评论区 · 非真实互动数据', 56, 144, 16, '#8FA3AA', 0, FMONO);

    const cardX = 48, cardW = W - 96, cardTop = 156, padX = 34;
    const innerW = cardW - padX * 2;
    const crowdTxt = '路人：「这条评论我先转给我那个十年没联系的朋友」';
    const replyTxt = c.mission.replace('你的友情通关提示：', '');
    const avail = H - cardTop - 300;

    const plan = (compact, withCrowd) => {
      const fs = compact ? 26 : 31, blh = compact ? 40 : 48, flh = compact ? 38 : 46;
      const pTop = compact ? 38 : 46, pBot = compact ? 20 : 26, gap = compact ? 12 : 18;
      const rows = [];
      (MEME2[c.id] || c.meme.split('\n')).forEach(line => {
        const who = line.split('：')[0];
        const txt = line.slice(who.length + 1);
        const you = (who === '你');
        const fs2 = you ? Math.round(fs * 1.28) : fs;
        const lh2 = you ? Math.round(blh * 1.28) : blh;
        font(ctx, fs2, FSANS, you ? '700' : '600');
        const n = wrapCJK(ctx, txt, innerW - 44, 2).length;
        rows.push({ kind: 'meme', label: who, txt, n, you, fs: fs2, lh: lh2, h: pTop + n * lh2 + pBot + (you ? 14 : 0) });
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
      const you = !!r.you;
      const bg = you ? NIGHT : (r.kind === 'reply' ? '#F6E4C9' : '#EDE3D2');
      const lb = you ? '#D9A05B' : (r.kind === 'meme' ? '#A88355' : '#7C8B93');
      const tc = you ? '#FFF4E2' : INK;
      rr(ctx, cardX + padX, cy, innerW, r.h, 18, bg);
      spaced(ctx, r.label, cardX + padX + 22, cy + P.pTop - 6, you ? 16 : 14, lb, you ? 3 : 1, FSANS);
      const lh = r.lh || (r.kind === 'meme' ? P.blh : P.flh);
      block(ctx, r.txt, cardX + padX + 22, cy + P.pTop + (you ? 50 : 50), innerW - 44, r.fs || P.fs, tc, FSANS, you ? '700' : '600', lh, you ? 2 : 3);
      cy += r.h + P.gap;
    });

    if (P.withCrowd) {
      rr(ctx, cardX + padX, cy, innerW, P.crowdH, 18, 'rgba(18,36,47,.06)');
      block(ctx, crowdTxt, cardX + padX + 22, cy + 46, innerW - 44, 20, '#5D6C72', FSANS, '400', 34, 2);
      cy += P.crowdH + 34;
    }

    spaced(ctx, '♡ 喜欢  ·  ↻ 分享给老友  ·  💬 友好留言', cardX + padX, cy, 18, '#8B9498', 1, FSANS);
    cy += 16;
    ctx.strokeStyle = 'rgba(18,36,47,.13)'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(cardX + padX, cy); ctx.lineTo(cardX + cardW - padX, cy); ctx.stroke();

    /* 标题、盖章、评论区入口依次排在卡片底部 */
    const cardBottom = cardTop + cardH;
    text(ctx, c.title, cardX + padX, cardBottom - 214, { size: 38, color: INK, ls: 1 });
    block(ctx, c.stamp, cardX + padX, cardBottom - 158, innerW - 40, 25, '#A88355', FSERIF, '400', 38, 2);
    rr(ctx, cardX + padX, cardBottom - 96, innerW, 46, 23, 'rgba(18,36,47,.05)');
    spaced(ctx, '评论区见 · 留下你的那句嘴硬  ›', cardX + padX + 84, cardBottom - 66, 14, '#7C8B93', 1, FSANS);

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

let posterPreviewObserver = null;
let posterPreviewScrollHandler = null;
function schedulePosterPreviews() {
  if (posterPreviewObserver) { posterPreviewObserver.disconnect(); posterPreviewObserver = null; }
  if (posterPreviewScrollHandler) {
    window.removeEventListener('scroll', posterPreviewScrollHandler);
    posterPreviewScrollHandler = null;
  }
  const chooser = document.getElementById('poster-chooser');
  if (!chooser) return;
  let started = false;
  const begin = () => {
    if (started) return;
    started = true;
    if (posterPreviewObserver) { posterPreviewObserver.disconnect(); posterPreviewObserver = null; }
    if (posterPreviewScrollHandler) {
      window.removeEventListener('scroll', posterPreviewScrollHandler);
      posterPreviewScrollHandler = null;
    }
    drawPreviews();
  };
  posterPreviewScrollHandler = () => {
    if (chooser.getBoundingClientRect().top < window.innerHeight + 300) begin();
  };
  if ('IntersectionObserver' in window) {
    posterPreviewObserver = new IntersectionObserver(entries => {
      if (entries.some(item => item.isIntersecting)) begin();
    }, { rootMargin: '300px 0px' });
    posterPreviewObserver.observe(chooser);
  }
  window.addEventListener('scroll', posterPreviewScrollHandler, { passive: true });
  posterPreviewScrollHandler();
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
function isWeChat() { return /MicroMessenger/i.test(navigator.userAgent || ''); }
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
      '<p>' + (isWeChat() ? '长按下面这张图 → <b>保存到相册</b>；长按没反应就直接<b>截屏</b>，发朋友圈效果一样。' : '点「下载原图」保存，或长按图片 → 保存到相册。') + '</p>' +
      '<div class="sheet-preview"><img id="sheet-img" alt="已生成的友情人物海报，可长按保存"></div>' +
      '<div class="sheet-actions">' + (isWeChat() ? '' : '<button class="btn btn--dark" id="sheet-share">系统分享 / 存储</button>') +
      '<a class="btn btn--ghost" id="sheet-file" download="' + e(filename) + '">下载原图</a></div>' +
      '<small>' + (isWeChat() ? '还是不行？点右上角 ⋯ → 在浏览器打开，再长按保存。' : '保存后在相册里就能直接发朋友圈。') + '</small>' +
    '</section>';
  document.body.appendChild(mask);

  const picture = mask.querySelector('#sheet-img');
  // 微信/iOS 不给 blob: 图片"保存到相册"，data URI 的成功率高得多；canvas 不再重复塞进弹层
  picture.src = canvas.toDataURL('image/jpeg', 0.92);
  mask.querySelector('#sheet-file').href = url;

  const close = () => { URL.revokeObjectURL(url); mask.remove(); document.removeEventListener('keydown', esc); };
  function esc(ev) { if (ev.key === 'Escape') close(); }
  document.addEventListener('keydown', esc);
  mask.querySelector('#sheet-close').onclick = close;
  mask.onclick = ev => { if (ev.target === mask) close(); };
  const shareBtn = mask.querySelector('#sheet-share');
  if (shareBtn) shareBtn.onclick = async () => {
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
  // Clear selections saved by earlier versions; every reload starts a fresh run.
  try { sessionStorage.removeItem('hhyq-progress'); } catch (err) { }
  try { localStorage.removeItem('hhyq-template'); } catch (err) { }
  try { portraitFocus = JSON.parse(localStorage.getItem('hhyq-focus') || '{}') || {}; } catch (err) { portraitFocus = {}; }
  const r = new URL(location.href).searchParams.get('r');
  if (r && C[r]) {
    current = C[r]; fromQuiz = false; renderResult();
    // Show the public portrait immediately; recover optional custom photo later.
    restorePhotos().then(() => {
      if (customPhotos[r] && current && current.id === r && !fromQuiz) renderResult();
    });
  } else {
    home();
    // Browser photo storage is optional and must never block the home screen.
    restorePhotos();
  }
}
window.addEventListener('popstate', () => {
  const r = new URL(location.href).searchParams.get('r');
  if (r && C[r]) { current = C[r]; fromQuiz = false; renderResult(); } else home();
});

/* Mobile photo recovery: use same-origin JPG cover when WebP is unavailable. */
document.addEventListener('error', event => {
  const img = event.target;
  if (!(img instanceof HTMLImageElement)) return;
  const id = img.getAttribute('data-hhyq-photo');
  if (!id || !photoSources[id]) return;
  if (img.dataset.hhyqFallback === '2') {
    img.classList.add('photo-unavailable');
    return;
  }
  if (img.dataset.hhyqFallback === '1') {
    img.dataset.hhyqFallback = '2';
    img.src = MEDIA_ROOT + 'share-cover-' + id + '.jpg';
    return;
  }
  img.dataset.hhyqFallback = '1';
  img.src = MEDIA_ROOT + 'photos-hd-jpeg/' + id + '.jpg';
}, true);

init();
