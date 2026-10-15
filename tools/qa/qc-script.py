# -*- coding: utf-8 -*-
"""G2 红线+体例质检脚本 v1（2026-10-11）——词表部分落地（连续三句同构、颜文字、现实影射与段方差指标留作人工复核）

配套：tools/qa/redline-wordlist.md 与 tools/qa/style-conventions.md
用法：
  python tools/qa/qc-script.py <章节文件> [--ch N] [--json]   # G2 扫描；--ch 用于字数目标切换（前5章 2200-2800 / 稳定期 2800-3500）
退出码：0=通过（可有 warning）；2=有 blocker（打回）；4=用法错误
计数口径：词频按出现次数；部位词预算 ≤0.5/万字 且单章 ≤1；⚑ 未裁边界词只告警不拦截。
"""
import argparse
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ── 词表（与 红线词表v1.md 同步维护；改词表必须同步这里）──
AI_TELLS = ['嘴角勾起', '嘴角上扬', '眼神深邃', '眼中闪过一丝', '微微挑眉', '沉吟片刻',
            '心中一凛', '心中一沉', '心中一动', '心下了然', '顿时', '瞬间', '愈发', '略微', '一时之间']
EMOTION_DIRECT = ['心里一酸', '心中一暖', '感到一阵', '意识到', '明白了', '松了一口气',
                  '小心翼翼地', '淡淡地', '深深地']
PORN_HARD = ['胸脯', '胸部', '大腿根部', '春光乍泄', '肌肤之亲', '浑圆', '酥胸', '玉体']
BODY_POOL_FLAG = ['锁骨', '香肩', '长腿', '脖颈', '下颌', '藕臂', '白皙', '肌肤']  # ⚑ 未裁
GHOST_WORDS = ['厉鬼', '冤魂', '恶灵附体', '闹鬼', '阴曹地府', '鬼']  # 鬼=单字告警，人工判语境
SELFHARM = ['割腕', '上吊', '安眠药', '跳楼']
CANNIBAL_TASTY = ['撕咬咀嚼', '鲜甜', '多汁']
NAME_POLLUTION = ['许七安', '张元清', '封不觉', '陈歌', '李东泽', '许平峰', '克莱恩', '韩立']
AUTHOR_VOICE = ['要知道', '所谓', '不得不说']
# 使用时替换为你自己作品的未成年角色名
MINORS = ['角色A', '角色B']  # 未成年角色（部位词 ±200 字一票否决）
PATTERN_BUSHI = re.compile(r'不是[^。！？]{1,30}而是')
PATTERN_YUQISHUO = re.compile(r'与其说[^。！？]{1,30}不如说')
PATTERN_PAIBI = re.compile(r'有[^，。！？]{1,8}，有[^，。！？]{1,8}，有')
PATTERN_DASH = re.compile(r'——|—')
PATTERN_ENQUOTE = re.compile(r'["\']')
PATTERN_ELLIPSE_BAD = re.compile(r'…{7,}')
PATTERN_CHAPTER_REF = re.compile(r'第[0-9一二三四五六七八九十百]{1,4}章')
PATTERN_EN_WORD = re.compile(r'[A-Za-z]{2,}')
PANEL_SPAN = re.compile(r'【[^】]*】')  # 面板/系统提示内豁免英文检查


def read_text(path):
    for enc in ('utf-8-sig', 'utf-8', 'gbk'):
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    with open(path, encoding='utf-8', errors='replace') as f:
        return f.read()


def strip_frontmatter(text):
    return re.sub(r'^---\s*\n.*?\n---\s*\n?', '', text, flags=re.S)


def cjk_len(t):
    return len(re.findall(r'[\u4e00-\u9fff]', t))


def snippet(t, idx, w):
    s = t[max(0, idx - 14):idx + len(w) + 14].replace('\n', '␤')
    return s.strip()


def hit_items(t, words, category, note, level):
    out = []
    for w in words:
        n = t.count(w)
        if n:
            i = t.find(w)
            out.append({'类': category, '词': w, '次数': n, '样例': snippet(t, i, w), '说明': note, '级别': level})
    return out


def scan(path, ch):
    raw = read_text(path)
    t = strip_frontmatter(raw)
    n_cjk = cjk_len(t)
    blockers, warnings = [], []

    # 一、AI 指纹词（命中即改写）
    blockers += hit_items(t, AI_TELLS, 'AI指纹词', '命中即改写', 'block')
    # 二、情绪直陈
    blockers += hit_items(t, EMOTION_DIRECT, '情绪直陈', '改为动作/对白/留白', 'block')
    # 三、句式红线
    for name, pat, note in [
        ('不是…而是', PATTERN_BUSHI, '每章 ≤1 次'),
        ('与其说…不如说', PATTERN_YUQISHUO, '零容忍'),
        ('排比三段(有X，有Y，有Z)', PATTERN_PAIBI, '零容忍'),
        ('破折号', PATTERN_DASH, '零容忍（——/—）'),
    ]:
        hits = list(pat.finditer(t))
        limit = 1 if name == '不是…而是' else 0
        if len(hits) > limit:
            h = hits[limit] if len(hits) > limit else hits[0]
            blockers.append({'类': '句式红线', '词': name, '次数': len(hits), '样例': snippet(t, h.start(), h.group(0)),
                             '说明': note, '级别': 'block'})
    # 四1、擦边直白（零容忍）
    blockers += hit_items(t, PORN_HARD, '擦边直白', '平台机审方向，零容忍', 'block')
    # 四2、⚑部位词预算池（未裁——只告警）；未成年 ±200 字 = 一票否决
    pool_hits = hit_items(t, BODY_POOL_FLAG, '部位词池⚑', '未裁边界词，占预算（≤0.5/万字·单章≤1）', 'warn')
    for w in BODY_POOL_FLAG:
        start = 0
        while True:
            i = t.find(w, start)
            if i < 0:
                break
            window = t[max(0, i - 200):i + 200 + len(w)]
            near = [m for m in MINORS if m in window]
            if near:
                blockers.append({'类': '未成年一票否决', '词': f'{w} × {"/".join(near)}', '次数': 1,
                                 '样例': snippet(t, i, w), '说明': '部位词落在未成年角色 ±200 字内（★一票否决）', '级别': 'block'})
            start = i + 1
    if pool_hits:
        total = sum(h['次数'] for h in pool_hits)
        budget = n_cjk * 0.5 / 10000
        if total > 1 or total > max(budget, 1.0):
            for h in pool_hits:
                h['说明'] += f'；本章合计 {total} 处已超预算'
        warnings += pool_hits
    # 四3、鬼神归因（告警，人工判语境：示例设定词/游戏机制放行）
    warnings += hit_items(t, GHOST_WORDS, '鬼神归因', '异常须归因游戏机制；示例设定词语境放行', 'warn')
    # 四5、自残（告警：静态痕迹放行，过程描写打回由人判）
    warnings += hit_items(t, SELFHARM, '自残/危险行为', '过程描写零容忍；静态痕迹放行——人工判', 'warn')
    # 四6、吃人写法（告警）
    warnings += hit_items(t, CANNIBAL_TASTY, '吃人特写', '过程特写/美味感官禁；前兆与剪影放行', 'warn')
    # 五、专名污染（零容忍）
    blockers += hit_items(t, NAME_POLLUTION, '专名污染', '微调语料主角名，历史污染名单', 'block')
    # 体例
    n_ex = t.count('！') + t.count('!')
    if n_ex > 8:
        warnings.append({'类': '体例', '词': '感叹号', '次数': n_ex, '样例': '', '说明': f'每章 ≤8，本章 {n_ex}', '级别': 'warn'})
    eq = [m for m in PATTERN_ENQUOTE.finditer(strip_panels(t))]
    if eq:
        warnings.append({'类': '体例', '词': '英文直引号', '次数': len(eq), '样例': snippet(t, eq[0].start(), eq[0].group(0)),
                         '说明': '对话用中文引号""', '级别': 'warn'})
    eb = PATTERN_ELLIPSE_BAD.findall(t)
    if eb:
        warnings.append({'类': '体例', '词': '省略号连用', '次数': len(eb), '样例': '', '说明': '……可用单次，禁连用', '级别': 'warn'})
    body = strip_panels(t)
    for m in PATTERN_CHAPTER_REF.finditer(body):
        warnings.append({'类': '体例', '词': '"第N章"入正文', '次数': 1, '样例': snippet(body, m.start(), m.group(0)),
                         '说明': '故事单元命名制', '级别': 'warn'})
        break
    enw = [m.group(0) for m in PATTERN_EN_WORD.finditer(body)]
    if enw:
        warnings.append({'类': '体例', '词': '英文字母串', '次数': len(enw), '样例': '、'.join(sorted(set(enw))[:6]),
                         '说明': '正文禁英文缩写/单词（【】面板内豁免）——人工判', '级别': 'warn'})
    av = sum(t.count(w) for w in AUTHOR_VOICE)
    if av * 10000 / max(n_cjk, 1) > 0.4:
        warnings.append({'类': '体例', '词': '作者腔', '次数': av, '样例': '',
                         '说明': f'要知道/所谓/不得不说 ≤0.4/万字，本章 {av * 10000 / max(n_cjk, 1):.2f}', '级别': 'warn'})
    # 字数目标
    lo, hi = (2200, 2800) if ch <= 5 else (2800, 3500)
    if not (lo <= n_cjk <= hi):
        warnings.append({'类': '字数', '词': f'{lo}-{hi}', '次数': n_cjk, '样例': '',
                         '说明': f'汉字数 {n_cjk} 超出第{ch}章目标区间', '级别': 'warn'})
    # info
    paras = [p for p in t.split('\n') if p.strip()]
    dlg_paras = [p for p in paras if re.search(r'[“"][^”"]{1,300}[”"]', p)]
    info = {'汉字数': n_cjk, '段数': len(paras),
            '对话段占比%': round(len(dlg_paras) / max(len(paras), 1) * 100, 1),
            '感叹号': n_ex, '破折号': len(PATTERN_DASH.findall(t)),
            '"吃人"字样': t.count('吃人')}
    return {'文件': path, '章号': ch, 'blockers': blockers, 'warnings': warnings, 'info': info,
            '判定': 'block' if blockers else 'pass'}


def strip_panels(t):
    return PANEL_SPAN.sub('【…】', t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('path', nargs='?')
    ap.add_argument('--ch', type=int, default=4)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    if not a.path:
        print(__doc__)
        sys.exit(4)
    if not os.path.isfile(a.path):
        print(json.dumps({'错误': f'稿件不存在：{a.path}', '判定': 'missing'}, ensure_ascii=False))
        sys.exit(4)
    r = scan(a.path, a.ch)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(f"== G2 质检 · 第{r['章号']}章 · 判定：{'❌ 打回' if r['blockers'] else '✅ 通过'} ==")
        for grp, items in [('❌ 拦截项', r['blockers']), ('⚠️ 告警项', r['warnings'])]:
            if items:
                print(f'\n{grp}（{len(items)}）')
                for it in items:
                    print(f"  [{it['类']}] {it['词']} ×{it['次数']} — {it['说明']}")
                    if it['样例']:
                        print(f"      …{it['样例']}…")
        print(f"\nInfo: {json.dumps(r['info'], ensure_ascii=False)}")
    sys.exit(2 if r['blockers'] else 0)


if __name__ == '__main__':
    main()
