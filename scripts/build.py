# -*- coding: utf-8 -*-
import json, io, sys, os, re, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
# 云端运行：本文件位于 repo/scripts/build.py，repo 根为上一级
base = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(base)

hot = json.load(open(os.path.join(root, 'hotdata.json'), encoding='utf-8'))
adv_data = json.load(open(os.path.join(root, 'adv.json'), encoding='utf-8'))
adv = adv_data['items']
RL_TOP3 = adv_data.get('rl_top3', [])
VS_TOP3 = adv_data.get('vs_top3', [])

# ---- integrity check ----
missing = []
for plat in ('douyin', 'weibo', 'xhs'):
    for it in hot[plat]:
        if it['title'] not in adv:
            missing.append(plat + '|' + it['title'])
if missing:
    print('MISSING ADVICE:', missing)
    sys.exit(1)
print('advice coverage OK:', sum(len(v) for v in hot.values()), 'items')

def fmt_hot(v):
    try:
        n = float(str(v).replace(',', ''))
    except Exception:
        return ''
    if n <= 0:
        return ''
    w = n / 10000.0
    if w >= 1000:
        return str(int(round(w))) + '万'
    if w >= 100:
        return ('%.1f' % w).rstrip('0').rstrip('.') + '万'
    return ('%.1f' % w).rstrip('0').rstrip('.') + '万'

def build(brand, meta):
    data = {}
    for plat in ('douyin', 'weibo', 'xhs'):
        rows = []
        for it in hot[plat]:
            a = adv[it['title']]
            tag, angle = a['rl'] if brand == 'rl' else a['vs']
            rows.append({
                'rank': it['rank'],
                'title': it['title'],
                'cat': a['cat'],
                'heat': fmt_hot(it['hot']),
                'sum': a['sum'],
                'tag': tag,
                'angle': angle,
            })
        rows.sort(key=lambda x: x['rank'])
        data[plat] = rows
    js = json.dumps(data, ensure_ascii=False)
    css = RL_CSS if brand == 'rl' else VS_CSS
    return render(meta, js, css)

RL_CSS = open(os.path.join(root, 'ralph-lauren', 'index.html'), encoding='utf-8').read()
RL_CSS = RL_CSS.split('</style>')[0].split('<style>')[1]

VS_CSS = r'''
  :root{
    --ink:#2A2130; --ink2:#17111B; --bg:#F8F4F3; --card:#FFFFFF;
    --rose:#CD4E43; --rose-deep:#A23A31; --red:#B03A2E;
    --text:#1A1B1C; --sub:#6B7280; --line:#E9DFE0;
  }
  *{margin:0;padding:0;box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{
    background:var(--bg);
    color:var(--text);
    font-family:'Noto Sans SC','PingFang SC','Microsoft YaHei',sans-serif;
    font-weight:400;
    line-height:1.6;
  }
  .wrap{max-width:1060px;margin:0 auto;padding:0 20px 48px;}

  /* ===== 头部 ===== */
  header{
    background:linear-gradient(135deg,#1A141D 0%,#120D16 100%);
    color:#F6EFED;padding:30px 0 26px;border-bottom:3px solid var(--rose);
  }
  .h-wrap{max-width:1060px;margin:0 auto;padding:0 20px;}
  .brand-line{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;}
  .brand-en{
    font-family:'Noto Serif SC',serif;font-size:26px;font-weight:700;
    letter-spacing:6px;color:#F6EFED;
  }
  .brand-cn{font-size:15px;letter-spacing:3px;color:#D9C6C2;}
  .brand-cn b{color:var(--rose);font-weight:500;}
  .meta-line{
    margin-top:10px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;
    font-size:12.5px;color:#B9AEB6;
  }
  .meta-line .dot{width:4px;height:4px;border-radius:50%;background:var(--rose);display:inline-block;}
  .tagline{
    margin-top:14px;font-family:'Noto Serif SC',serif;font-size:17px;color:#F6EFED;
    letter-spacing:2px;
  }
  .tagline em{font-style:normal;color:var(--rose);}
  .assets{
    margin-top:14px;display:flex;flex-wrap:wrap;gap:6px;
  }
  .asset{
    font-size:11px;border:1px solid rgba(246,239,237,.35);color:#D9C6C2;
    border-radius:999px;padding:2px 10px;letter-spacing:.5px;
  }
  .asset.on{border-color:var(--rose);color:var(--rose);}

  /* ===== 章节标题 ===== */
  .sec-title{
    margin:34px 0 14px;display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;
  }
  .sec-title h2{
    font-family:'Noto Serif SC',serif;font-size:20px;font-weight:600;color:var(--ink);
  }
  .sec-title span{font-size:12px;color:var(--sub);}

  /* ===== TOP3 ===== */
  .top3{display:flex;gap:14px;flex-wrap:wrap;}
  .t3{
    flex:1 1 280px;min-width:0;background:var(--card);border:1px solid var(--line);
    border-top:3px solid var(--rose);border-radius:10px;padding:16px 16px 14px;
    display:flex;flex-direction:column;gap:6px;
  }
  .t3 .no{font-family:'Noto Serif SC',serif;font-size:12px;color:var(--rose-deep);letter-spacing:1px;}
  .t3 h3{font-size:16px;font-weight:600;color:var(--ink);}
  .t3 .src{font-size:11.5px;color:var(--sub);}
  .t3 .tact{font-size:12.5px;color:var(--text);border-top:1px dashed var(--line);padding-top:8px;margin-top:2px;}
  .t3 .tact b{color:var(--rose-deep);font-weight:600;}

  /* ===== 看板控制 ===== */
  .controls{
    background:var(--card);border:1px solid var(--line);border-radius:10px;
    padding:12px 14px;display:flex;flex-direction:column;gap:10px;margin-bottom:16px;
  }
  .tabs{display:flex;gap:8px;flex-wrap:wrap;}
  .tab{
    font-size:13px;padding:6px 18px;border-radius:8px;border:1px solid var(--line);
    background:#FDFBFA;color:var(--ink);cursor:pointer;transition:all .15s;
    font-family:'Noto Sans SC',sans-serif;
  }
  .tab.active{background:var(--ink);color:#F6EFED;border-color:var(--ink);}
  .chips{display:flex;gap:6px;flex-wrap:wrap;}
  .chip{
    font-size:11.5px;padding:3px 11px;border-radius:999px;border:1px solid var(--line);
    background:#FDFBFA;color:var(--sub);cursor:pointer;transition:all .15s;
  }
  .chip.active{background:var(--rose);color:#fff;border-color:var(--rose);}
  .count-hint{font-size:11.5px;color:var(--sub);}
  .ctrl-row{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
  .ctrl-label{font-size:11.5px;color:var(--sub);white-space:nowrap;letter-spacing:1px;}
  .chips .cnt{font-size:10.5px;opacity:.8;margin-left:4px;}

  /* ===== 热点卡片 ===== */
  .card{
    background:var(--card);border:1px solid var(--line);border-radius:10px;
    padding:14px 16px;margin-bottom:12px;
  }
  .card-head{display:flex;gap:12px;align-items:flex-start;}
  .rank{
    font-family:'Noto Serif SC',serif;font-size:22px;font-weight:700;color:var(--ink);
    line-height:1;min-width:34px;padding-top:2px;
  }
  .card-title{font-size:15.5px;font-weight:600;color:var(--ink);line-height:1.4;}
  .card-meta{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:5px;}
  .chip-cat{
    font-size:11px;background:rgba(42,33,48,.08);color:var(--ink);
    border-radius:999px;padding:1px 9px;
  }
  .heat{
    font-size:11px;background:rgba(205,78,67,.14);color:var(--rose-deep);
    border-radius:999px;padding:1px 9px;font-weight:500;
  }
  .heat.na{background:rgba(107,114,128,.12);color:var(--sub);}
  .sum{font-size:12.5px;color:var(--sub);margin-top:9px;line-height:1.65;}
  .angle{
    margin-top:9px;background:#FCF7F5;border-left:3px solid var(--rose);
    border-radius:0 8px 8px 0;padding:8px 12px;font-size:12.5px;color:var(--text);
    line-height:1.65;
  }
  .angle b{color:var(--rose-deep);font-weight:600;}
  .angle.guard{border-left-color:var(--red);background:#FBF5F2;}
  .angle.guard b{color:var(--red);}
  .angle.no{border-left-color:#9aa1a9;background:#f7f8f9;}
  .angle.no b{color:#5b6470;}

  /* ===== 底部 ===== */
  footer{
    margin-top:34px;border-top:1px solid var(--line);padding-top:16px;
    font-size:11.5px;color:var(--sub);line-height:1.8;
  }
  footer b{color:var(--ink);font-weight:600;}
  .empty{text-align:center;color:var(--sub);padding:40px 0;font-size:13px;}

  @media (max-width:520px){
    .brand-en{font-size:21px;letter-spacing:4px;}
    .tagline{font-size:15px;}
    .sec-title h2{font-size:18px;}
    .card-title{font-size:14.5px;}
    .rank{font-size:19px;min-width:28px;}
  }
'''

TPL = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{TITLE} · 2026-09-09</title>
<link rel="stylesheet" href="https://miaoda.feishu.cn/fonts/css2?family=Noto+Serif+SC:wght@500;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap">
<style>
{css}
</style>
</head>
<body>

<header>
  <div class="h-wrap">
    <div class="brand-line">
      <span class="brand-en">{EN}</span>
      <span class="brand-cn">{CN} · <b>热点借势看板</b></span>
    </div>
    <div class="meta-line">
      <span>2026年9月9日 星期三</span><span class="dot"></span>
      <span>数据源：抖音热榜 / 小红书热搜 / 微博热搜</span><span class="dot"></span>
      <span>每日 10:00 自动更新</span>
    </div>
    <div class="tagline">{TAGLINE}</div>
    <div class="assets">
{ASSETS}
    </div>
  </div>
</header>

<main class="wrap">

  <section class="sec-title">
    <h2>今日品牌借势 TOP3</h2>
    <span>综合「平台热度 × 品牌契合度」选取，运营优先执行</span>
  </section>
  <section class="top3" id="top3"></section>

  <section class="sec-title">
    <h2>分平台热点 × 借势建议</h2>
    <span>完整收录当日三平台热榜（抖音 50 / 微博 50 / 小红书 20），按各平台原始排名展示，不做筛选；每条建议由运营团队基于品牌资产生成，发布前请运营与合规审核</span>
  </section>

  <div class="controls">
    <div class="tabs" id="tabs"></div>
    <div class="ctrl-row"><span class="ctrl-label">推荐类型</span><div class="chips" id="rec-chips"></div></div>
    <div class="ctrl-row"><span class="ctrl-label">内容类型</span><div class="chips" id="cat-chips"></div></div>
    <div class="count-hint" id="count"></div>
  </div>

  <section id="list"></section>

  <footer>
    <b>数据说明</b>：本看板完整收录当日三平台热榜全部条目（抖音 50 条 / 微博 50 条 / 小红书 20 条），未做筛选，按各平台原始榜单排名展示；榜单抓取自公开聚合源（86TOOL hot-rank 抖音/微博/小红书热搜榜），抓取时间 2026-09-09 傍晚；热度值为各源参考值，随榜单实时波动。<br>
    <b>借势建议</b>：依据品牌资产按话题分类模板生成；「借势角度」为强相关/可承接话题，「不推荐借势」为弱相关话题并附客观理由，「克制建议」为敏感或社会事件，建议不借势或经合规审批后低调执行。<br>
    <b>更新机制</b>：本看板每日 10:00 自动重跑生成当日版本，数据与建议随当日热榜更新。
  </footer>
</main>

<script>
(function(){{
  "use strict";
  var DATA = {DATA};
  var CATS = {CATS};
  var PLATS = [
    {{key:"douyin", name:"抖音热点"}},
    {{key:"xhs", name:"小红书热搜"}},
    {{key:"weibo", name:"微博热搜"}}
  ];
  var state = {{plat:"douyin", rec:"全部", cat:"全部"}};
  var RECS = [
    {{key:"全部", label:"全部"}},
    {{key:"angle", label:"借势角度"}},
    {{key:"no", label:"不推荐借势"}},
    {{key:"guard", label:"克制建议"}}
  ];

  function el(tag, cls, html){{
    var e = document.createElement(tag);
    if(cls) e.className = cls;
    if(html !== undefined) e.innerHTML = html;
    return e;
  }}

  function top3HTML(){{
    var items = {TOP3};
    var box = document.getElementById("top3");
    items.forEach(function(it){{
      var c = el("div","t3");
      c.appendChild(el("div","no",it.no));
      c.appendChild(el("h3",null,it.title));
      c.appendChild(el("div","src",it.src));
      c.appendChild(el("div","tact","<b>策略</b>：" + it.tact));
      box.appendChild(c);
    }});
  }}

  function renderTabs(){{
    var box = document.getElementById("tabs");
    PLATS.forEach(function(p){{
      var t = el("button","tab",p.name + " <span style='font-size:11px;opacity:.75'>" + DATA[p.key].length + "</span>");
      if(p.key === state.plat) t.classList.add("active");
      t.onclick = function(){{
        state.plat = p.key; state.cat = "全部";
        renderAll();
      }};
      box.appendChild(t);
    }});
  }}

  function renderRecChips(){{
    var box = document.getElementById("rec-chips");
    var arr = DATA[state.plat] || [];
    var cnt = {{}};
    arr.forEach(function(x){{ cnt[x.tag] = (cnt[x.tag]||0) + 1; }});
    RECS.forEach(function(r){{
      var n = r.key === "全部" ? arr.length : (cnt[r.key] || 0);
      if(r.key !== "全部" && n === 0) return;
      var ch = el("button","chip", r.label + "<span class='cnt'>" + n + "</span>");
      if(state.rec === r.key) ch.classList.add("active");
      ch.onclick = function(){{
        state.rec = r.key;
        renderAll();
      }};
      box.appendChild(ch);
    }});
  }}

  function renderCatChips(){{
    var box = document.getElementById("cat-chips");
    var arr = DATA[state.plat] || [];
    var cnt = {{}};
    arr.forEach(function(x){{ cnt[x.cat] = (cnt[x.cat]||0) + 1; }});
    var all = el("button","chip", "全部<span class='cnt'>" + arr.length + "</span>");
    if(state.cat === "全部") all.classList.add("active");
    all.onclick = function(){{
      state.cat = "全部";
      renderAll();
    }};
    box.appendChild(all);
    CATS.forEach(function(c){{
      var n = cnt[c] || 0;
      if(n === 0) return;
      var ch = el("button","chip", c + "<span class='cnt'>" + n + "</span>");
      if(state.cat === c) ch.classList.add("active");
      ch.onclick = function(){{
        state.cat = c;
        renderAll();
      }};
      box.appendChild(ch);
    }});
  }}

  function cardHTML(it){{
    var rank = (it.rank < 10 ? "0" : "") + it.rank;
    var heatEl = it.heat ? el("span","heat",it.heat) : el("span","heat na","热榜");
    var cls = "angle", label = "借势角度";
    if(it.tag === "no"){{ cls = "angle no"; label = "不推荐借势"; }}
    if(it.tag === "guard"){{ cls = "angle guard"; label = "克制建议"; }}
    var card = el("article","card");
    var head = el("div","card-head");
    head.appendChild(el("span","rank",rank));
    var tw = el("div");
    tw.style.minWidth = "0";
    tw.appendChild(el("div","card-title",it.title));
    var meta = el("div","card-meta");
    meta.appendChild(el("span","chip-cat",it.cat));
    meta.appendChild(heatEl);
    tw.appendChild(meta);
    head.appendChild(tw);
    card.appendChild(head);
    card.appendChild(el("p","sum",it.sum));
    card.appendChild(el("div",cls,"<b>" + label + "</b>　" + it.angle));
    return card;
  }}

  function renderList(){{
    var box = document.getElementById("list");
    box.innerHTML = "";
    var arr = DATA[state.plat] || [];
    var list = arr.filter(function(x){{
      var okCat = state.cat === "全部" || x.cat === state.cat;
      var okRec = state.rec === "全部" || x.tag === state.rec;
      return okCat && okRec;
    }});
    document.getElementById("count").textContent = "共 " + list.length + " 条";
    if(!list.length){{
      box.appendChild(el("div","empty","该分类下暂无条目"));
      return;
    }}
    list.forEach(function(it){{ box.appendChild(cardHTML(it)); }});
  }}

  function renderAll(){{
    var t = document.getElementById("tabs");
    var rc = document.getElementById("rec-chips");
    var cc = document.getElementById("cat-chips");
    t.innerHTML = ""; rc.innerHTML = ""; cc.innerHTML = "";
    renderTabs(); renderRecChips(); renderCatChips(); renderList();
  }}

  try {{
    top3HTML();
    renderAll();
  }} catch(e){{
    var box = document.getElementById("list");
    box.innerHTML = '<div class="empty">页面渲染异常：' + e.message + '</div>';
  }}
}})();
</script>
</body>
</html>
'''

def render(meta, data_js, css):
    assets = '\n'.join('      <span class="asset%s">%s</span>' % (' on' if a[1] else '', a[0]) for a in meta['assets'])
    cats = ["全部","时尚穿搭","体育赛事","影视综艺","情感话题","生活方式","知识科普","社会事件","科技财经","美食探店","娱乐八卦"]
    now = datetime.datetime.now()
    date_cn = '%d年%d月%d日 星期%s' % (now.year, now.month, now.day, '一二三四五六日'[now.weekday()])
    date_iso = '%04d-%02d-%02d' % (now.year, now.month, now.day)
    out = TPL.format(
        TITLE=meta['title'], EN=meta['en'], CN=meta['cn'], TAGLINE=meta['tagline'],
        ASSETS=assets, DATA=data_js,
        CATS=json.dumps(cats, ensure_ascii=False),
        TOP3=json.dumps(meta['top3'], ensure_ascii=False),
        css=css,
    )
    out = out.replace('2026年9月9日 星期三', date_cn)
    out = out.replace('2026-09-09', date_iso)
    out = out.replace('傍晚', '上午')
    return out

rl_meta = {
    'title': '拉夫劳伦 × 全平台热点借势看板',
    'en': 'RALPH LAUREN', 'cn': '拉夫劳伦',
    'tagline': '永不过时的经典 —— 品牌 × 全平台每日热点结合',
    'assets': [
        ('核心单品：Polo 衫 / 牛津衬衫 / 绞花针织 / 西装 / 大衣 / 牛仔', 0),
        ('风格：美式经典 · 老钱风 · 常春藤学院风 · 静奢', 0),
        ('背书：温网官方服装品牌（2006 年至今）', 0),
        ('副线：Polo / Purple Label / RRL / RLX / Lauren', 1),
    ],
    'top3': RL_TOP3,
}

vs_meta = {
    'title': '维密 × 全平台热点借势看板',
    'en': "VICTORIA'S SECRET", 'cn': '维多利亚的秘密',
    'tagline': '性感自信 · 闪耀如你 —— 品牌 × 全平台每日热点结合',
    'assets': [
        ('睡衣：光泽感面料 · 高级感垂坠 · 杨幂同款', 0),
        ('水钻内衣（含 OG 水钻系列）：闪钻肩带 · 薄杯 · 聚拢', 0),
        ('三角杯（含 ACE 系列）：字母 logo 肩带 · 蕾丝 · 无钢圈', 0),
        ('场景：居家 · 约会 · 旅行 · 睡眠', 1),
    ],
    'top3': VS_TOP3,
}

rl_html = build('rl', rl_meta)
vs_html = build('vs', vs_meta)

out_files = [
    (os.path.join(root, 'ralph-lauren', 'index.html'), rl_html),
    (os.path.join(root, 'victorias-secret', 'index.html'), vs_html),
]
for path, content in out_files:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('written:', path, len(content))
