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
MODEL = os.environ.get('ARK_MODEL', 'doubao-seed-1-6-250615')

RL_BRIEF = """品牌：拉夫劳伦（男女装），主打「永不过时的经典」。
产品线：Polo/Purple Label/RRL/RLX/Lauren；风格：美式经典/老钱风/常春藤学院风/静奢；背书：温网官方服装品牌（2006 年至今）。
注意：郑钦文不是品牌代言人，措辞禁止出现「代言人」；明星无合作不借肖像。"""

VS_BRIEF = """品牌：维多利亚的秘密。
产品卖点：睡衣（光泽感面料/高级感垂坠/杨幂同款，场景居家/睡眠）、水钻内衣含 OG 水钻系列（闪钻肩带/薄杯/聚拢，场景约会）、三角杯含 ACE 系列（字母logo肩带/蕾丝/无钢圈）。
注意：每条建议聚焦单一产品线，不堆叠；杨幂同款是自有卖点可提；明星无合作不借肖像。"""

RULES = """给每条热榜条目生成借势建议，规则：
1) tag 三选一：angle=强相关可借势（给具体内容落点）；no=弱相关/无承接（给客观理由，不硬蹭）；guard=敏感/灾害/恶性/重大事件（给克制口径，不借势不评论）。
2) cat 分类（十选一）：时尚穿搭/体育赛事/影视综艺/情感话题/生活方式/知识科普/社会事件/科技财经/美食探店/娱乐八卦。
3) sum：一句话客观摘要（不含观点）。
4) angle 文案：具体、可执行（内容形式+平台+KOL方向+聚焦的产品线），30-60字，不出现"绝对/第一/最"等绝对化表述。
5) 不硬蹭：数码/游戏/宠物/纯娱乐等无承接的标 no；政治外交/灾害/医疗个案/人物离世/社会争议标 guard。
6) 同时给两个品牌：rl（拉夫劳伦）与 vs（维密）各一套 tag+angle。
另需生成 rl_top3 / vs_top3：各选今日最适合借势的 3 条（综合热度与契合度），每项 {no:"借势机会 01..03", title:"短标题", src:"引用上榜话题与热度", tact:"策略60-90字"}。
只输出 JSON，不要多余文字。JSON 结构：
{"items":{"标题":{"cat":"..","sum":"..","rl":["angle",".."],"vs":["no",".."]}},"rl_top3":[...],"vs_top3":[...]}"""

def call_llm(messages):
    body = json.dumps({
        'model': MODEL,
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 8000,
    }).encode('utf-8')
    req = urllib.request.Request(API_URL, data=body, method='POST', headers={
        'Authorization': 'Bearer ' + os.environ['ARK_API_KEY'],
        'Content-Type': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.loads(r.read().decode('utf-8'))
    return resp['choices'][0]['message']['content']

def extract_json(text):
    m = re.search(r'\{.*\}', text, re.S)
    return json.loads(m.group(0))

def main():
    hot = json.load(open(os.path.join(ROOT, 'hotdata.json'), encoding='utf-8'))
    items, tops = {}, {'rl_top3': [], 'vs_top3': []}
    for plat in ('douyin', 'weibo', 'xhs'):
        rows = hot[plat]
        prompt = RULES + '\n\n【' + plat + ' 热榜 ' + str(len(rows)) + ' 条】\n'
        for it in rows:
            prompt += '%d. %s（热度 %s）\n' % (it['rank'], it['title'], it['hot'])
        for attempt in range(3):
            try:
                out = extract_json(call_llm([
                    {'role': 'system', 'content': '你是资深品牌营销借势策划，客观理性，不为蹭而蹭。'},
                    {'role': 'user', 'content': '【拉夫劳伦】' + RL_BRIEF + '\n【维密】' + VS_BRIEF + '\n\n' + prompt},
                ]))
                for title, v in out['items'].items():
                    v.setdefault('cat', '生活方式'); v.setdefault('sum', '')
                    v.setdefault('rl', ['no', '无产品承接点，建议不借势。'])
                    v.setdefault('vs', ['no', '无产品承接点，建议不借势。'])
                    items[title] = v
                if plat == 'weibo':  # 只在最后一个平台收集 top3
                    tops['rl_top3'] = out.get('rl_top3', [])[:3]
                    tops['vs_top3'] = out.get('vs_top3', [])[:3]
                break
            except Exception as e:
                print('retry %s attempt %d: %s' % (plat, attempt + 1, e))
                time.sleep(5)
        else:
            raise SystemExit('LLM 建议生成失败: ' + plat)

    # 校验覆盖
    missing = []
    for plat in ('douyin', 'weibo', 'xhs'):
        for it in hot[plat]:
            if it['title'] not in items:
                missing.append(plat + '|' + it['title'])
    if missing:
        print('MISSING:', missing)
        raise SystemExit('建议覆盖不完整')
    print('advice coverage OK:', sum(len(v) for v in hot.values()), 'items')
    out = {'items': items, 'rl_top3': tops['rl_top3'], 'vs_top3': tops['vs_top3']}
    with open(os.path.join(ROOT, 'adv.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('saved', os.path.join(ROOT, 'adv.json'))

if __name__ == '__main__':
    if not os.environ.get('ARK_API_KEY'):
        raise SystemExit('缺少 ARK_API_KEY 环境变量')
    main()
