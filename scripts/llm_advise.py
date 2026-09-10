# -*- coding: utf-8 -*-
"""云端 LLM 建议生成：读取 repo 根/hotdata.json，调用方舟 Ark API 生成双品牌借势建议 -> repo 根/adv.json
adv.json 结构:
{
  "items": { "标题": {"cat": "...", "sum": "...", "rl": ["tag", "angle"], "vs": ["tag", "angle"]}, ... },
  "rl_top3": [ {"no": "...", "title": "...", "src": "...", "tact": "..."} x3 ],
  "vs_top3": [ ... x3 ]
}
"""
import os, json, re, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_URL = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
MODEL = os.environ.get('ARK_MODEL', 'ep-20260910121246-2xkh5')

RL_BRIEF = """品牌：拉夫劳伦（男女装），主打「永不过时的经典」。
产品线：Polo/Purple Label/RRL/RLX/Lauren；风格：美式经典/老钱风/常春藤学院风/静奢；背书：温网官方服装品牌（2006 年至今）。
注意：郑钦文不是品牌代言人，措辞禁止出现「代言人」；明星无合作不借肖像。"""

VS_BRIEF = """品牌：维多利亚的秘密。
产品卖点：睡衣（光泽感面料/高级感垂坠/杨幂同款，场景居家/睡眠）、水钻内衣含 OG 水钻系列（闪钻肩带/薄杯/聚拢，场景约会）、三角杯含 ACE 系列（字母logo肩带/蕾丝/无钢圈）。
注意：每条建议聚焦单一产品线，不堆叠；杨幂同款是自有卖点可提；明星无合作不借肖像。"""

RULES = """你是资深品牌营销借势策划，为拉夫劳伦和维密两个品牌生成每日热榜借势建议。要求客观理性、有策略深度，不为蹭而蹭。

【核心规则】
1) tag 三选一：
   - angle=强相关可借势（必须给具体内容落点和策略，并生成 content_template 内容模板）
   - no=弱相关/无承接（给客观理由，说明为什么不适合借势，不生成 content_template）
   - guard=敏感/灾害/恶性/重大事件（给克制口径，不借势不评论，不生成 content_template）
2) cat 分类（十选一）：时尚穿搭/体育赛事/影视综艺/情感话题/生活方式/知识科普/社会事件/科技财经/美食探店/娱乐八卦
3) sum：一句话客观摘要（不含观点，20字内）

【angle 文案要求 —— 必须有深度，禁止泛泛而谈】
每条 angle 建议必须包含以下要素（60-100字），直接写策略，不要写"平台匹配XX"这种元信息前缀：
- 内容形式：根据当前平台选择——抖音=短视频，小红书=图文笔记，微博=话题+图文（绝对不能跨平台）
- KOL方向：根据当前平台选择——抖音=抖音XX垂类博主，小红书=小红书XX博主，微博=微博XXKOL
- 具体切入角度：说明从什么点结合（色系/场景/情绪/功能/人群/节日），不是"邀请博主分享"这种空话
- 产品卖点结合：明确用哪条产品线/哪个卖点，说明为什么这个热点和这个产品有关联
- 可执行内容方向：如"可可系老钱风穿搭公式"、"开箱→上身→夜景光泽"、"色系穿搭合集"
- 每条聚焦单一产品线，不堆叠

【content_template 内容模板 —— 仅 angle 类型必须生成，no/guard 不生成】
每条 angle 必须附带 content_template 对象，站在整个品牌维度和营销角度、平台契合度深入分析：
{
  "titles": ["标题1", "标题2", "标题3"],  // 3个内容标题建议，符合平台调性（抖音口语化有钩子，小红书种草感，微博话题感）
  "copy_direction": "文案方向：...",  // 50-80字，说明正文怎么写，开头钩子+中间卖点+结尾引导，结合平台用户阅读习惯
  "tags": ["#标签1", "#标签2", "#标签3"],  // 3-5个推荐标签/话题，平台热搜词+品牌词+品类词组合
  "distribution": "内容分发策略：...",  // 80-120字，站在整个品牌维度思考：①官方号怎么发（品牌官号发布什么内容、什么形式、什么时间点、如何借势话题）②KOL达人怎么合作（找什么类型/量级/调性的达人，合作形式是植入/共创/挑战赛）③UGC怎么引导（如何设计话题/互动机制引导用户自发参与和二次传播），三者如何组合形成传播矩阵
  "marketing_analysis": "营销分析：...",  // 80-120字，站在营销角度分析：为什么这个热点值得借势？目标受众是谁？传播逻辑是什么？能解决品牌什么问题（认知/种草/转化/品牌调性/用户互动）？短期和长期价值分别是什么？
  "platform_fit": "平台契合度：..."  // 60-100字，分析这个热点在当前平台的传播特点、用户参与方式、内容形式偏好、算法推荐逻辑，以及品牌内容如何适配平台调性和用户习惯，官方号和达人内容在该平台的差异化策略
}

【不硬蹭规则】
- 数码/游戏/宠物/纯娱乐/社会新闻等无产品承接的标 no，给客观理由
- 政治外交/灾害/医疗个案/人物离世/社会争议标 guard，不借势
- 教师节/节日等场景：拉夫可做礼赠，维密克制（内衣不适合送老师）
- 明星无合作不借肖像；郑钦文非拉夫代言人，禁出现"代言人"表述

【同时给两个品牌】rl（拉夫劳伦）与 vs（维密）各一套 tag+angle。维密更克制（内衣品类借势门槛高），angle 数量应明显少于拉夫。

【TOP3 生成】
rl_top3 / vs_top3：各选今日最适合借势的 3 条（综合热度×契合度×可执行性），每项：
- no: "借势机会 01/02/03"
- title: 短标题（8字内，有策略感）
- src: 引用上榜话题与热度（如"抖音「XX」1200万"）
- tact: 策略80-120字，说明核心创意、内容形式、平台、KOL方向、预期效果

【输出格式】
只输出 JSON，不要多余文字。结构：
{"items":{"标题":{"cat":"..","sum":"..","rl":["angle","..",{"content_template对象"}], "vs":["no",".."]}},"rl_top3":[...],"vs_top3":[...]}
注意：rl/vs 数组第三个元素 content_template 仅当 tag=angle 时存在，tag=no/guard 时数组只有两个元素。"""

def call_llm(messages):
    body = json.dumps({
        'model': MODEL,
        'messages': messages,
        'temperature': 0.3,
        'max_tokens': 12000,
    }).encode('utf-8')
    req = urllib.request.Request(API_URL, data=body, method='POST', headers={
        'Authorization': 'Bearer ' + os.environ['ARK_API_KEY'],
        'Content-Type': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.loads(r.read().decode('utf-8'))
    return resp['choices'][0]['message']['content']

def extract_json(text):
    # 去掉 markdown 代码块标记
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text.strip())
    m = re.search(r'\{.*\}', text, re.S)
    raw = m.group(0)
    try:
        return json.loads(raw)
    except Exception:
        # 容错：修复字符串内未转义的双引号（简单启发式）
        fixed = re.sub(r'(?<!\\)"(?=\s*[,\}\]])', '"', raw)  # no-op placeholder
        # 尝试逐键修复：把 value 里的裸引号转义
        try:
            return json.loads(raw)
        except Exception:
            # 最后手段：用正则提取所有 "title": {...} 对
            items = {}
            for mm in re.finditer(r'"([^"]+)"\s*:\s*\{([^{}]*)\}', raw):
                k, v = mm.group(1), mm.group(2)
                try:
                    items[k] = json.loads('{' + v + '}')
                except Exception:
                    pass
            if items:
                return {'items': items}
            raise

def main():
    hot = json.load(open(os.path.join(ROOT, 'hotdata.json'), encoding='utf-8'))
    items, tops = {}, {'rl_top3': [], 'vs_top3': []}
    plat_meta = {
        'douyin': ('抖音', '抖音短视频', '抖音垂类博主'),
        'weibo': ('微博', '微博话题+图文', '微博KOL'),
        'xhs': ('小红书', '小红书图文笔记', '小红书博主'),
    }
    for plat in ('douyin', 'weibo', 'xhs'):
        pname, pform, pkol = plat_meta[plat]
        rows = hot[plat]
        prompt = RULES + '\n\n【' + pname + '热榜 ' + str(len(rows)) + ' 条】以下所有条目均来自' + pname + '平台，借势建议必须使用' + pform + '形式和' + pkol + '，绝对不能跨平台。\n'
        for it in rows:
            prompt += '%d. %s（热度 %s）\n' % (it['rank'], it['title'], it['hot'])
        for attempt in range(3):
            try:
                out = extract_json(call_llm([
                    {'role': 'system', 'content': '你是资深品牌营销借势策划，客观理性，不为蹭而蹭。当前处理的是' + pname + '热榜，所有建议必须用' + pform + '和' + pkol + '。'},
                    {'role': 'user', 'content': '【拉夫劳伦】' + RL_BRIEF + '\n【维密】' + VS_BRIEF + '\n\n' + prompt},
                ]))
                for title, v in out['items'].items():
                    v.setdefault('cat', '生活方式'); v.setdefault('sum', '')
                    v.setdefault('rl', ['no', '无产品承接点，建议不借势。'])
                    v.setdefault('vs', ['no', '无产品承接点，建议不借势。'])
                    items[title] = v
                if plat == 'xhs':  # 在最后一个平台收集 top3
                    tops['rl_top3'] = out.get('rl_top3', [])[:3]
                    tops['vs_top3'] = out.get('vs_top3', [])[:3]
                break
            except Exception as e:
                print('retry %s attempt %d: %s' % (plat, attempt + 1, e))
                time.sleep(5)
        else:
            raise SystemExit('LLM 建议生成失败: ' + plat)

    # 校验覆盖，缺失条目自动补 fallback（不中断）
    missing = []
    for plat in ('douyin', 'weibo', 'xhs'):
        for it in hot[plat]:
            if it['title'] not in items:
                missing.append(plat + '|' + it['title'])
                items[it['title']] = {
                    'cat': '生活方式', 'sum': it['title'],
                    'rl': ['no', '无明确产品承接点，客观评估后建议不借势。'],
                    'vs': ['no', '无明确产品承接点，客观评估后建议不借势。'],
                }
    if missing:
        print('WARN missing %d items, auto-filled as no-recommend:' % len(missing), missing[:5])
    print('advice coverage OK:', sum(len(v) for v in hot.values()), 'items')
    out = {'items': items, 'rl_top3': tops['rl_top3'], 'vs_top3': tops['vs_top3']}
    with open(os.path.join(ROOT, 'adv.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('saved', os.path.join(ROOT, 'adv.json'))

if __name__ == '__main__':
    if not os.environ.get('ARK_API_KEY'):
        raise SystemExit('缺少 ARK_API_KEY 环境变量')
    main()
