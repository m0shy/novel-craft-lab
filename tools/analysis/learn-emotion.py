# -*- coding: utf-8 -*-
"""深度学习五书：情绪到底是"直说"还是"藏动作"？找实证

用法示例：python tools/analysis/learn-emotion.py --lib ./corpus/
（--lib 为语料根目录，其下按《书名》子目录定位 txt；含"恐怖屋/三个月"关键字的子目录整目录加载）
"""
import argparse
import os
import random
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
random.seed(7)

ap = argparse.ArgumentParser(description='情绪表达密度与例句抽样（五书对照）')
ap.add_argument('--lib', default='./corpus/', help='语料根目录（其下按《书名》子目录组织）')
args = ap.parse_args()
LIB = args.lib

BOOKS = {
    '灵境行者': [os.path.join(LIB, '《灵境行者》', '灵境行者(1-500章).txt'),
               os.path.join(LIB, '《灵境行者》', '灵境行者(501-1000章).txt')],
    '大奉打更人': [os.path.join(LIB, '《大奉打更人》', '_全本合并.txt')],
    '玩家凶猛': [os.path.join(LIB, '《玩家凶猛》', '玩家凶猛.txt')],
    '恐怖屋': [],
    '还剩三个月': [],
}

# 找恐怖屋和还剩三个月（根目录下含关键字的子目录，读其中全部 txt）
if os.path.isdir(LIB):
    for d in sorted(os.listdir(LIB)):
        if '恐怖屋' in d or '三个月' in d:
            txts = [os.path.join(LIB, d, f) for f in os.listdir(os.path.join(LIB, d)) if f.endswith('.txt')]
            if '恐怖屋' in d: BOOKS['恐怖屋'] = txts
            if '三个月' in d: BOOKS['还剩三个月'] = txts

def load(paths):
    text = ''
    for p in paths:
        try:
            for enc in ('utf-8', 'gbk', 'utf-16'):
                try:
                    with open(p, encoding=enc) as f:
                        text += f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
        except OSError:
            continue
    return text

DATA = {name: load(paths) for name, paths in BOOKS.items() if paths}

print('已加载：', {k: len(re.findall(r'[\u4e00-\u9fff]', v)) for k, v in DATA.items()})

# ── 1. 情绪直给词的真实密度（我上轮判"AI标签"，先看大师用不用） ──
EMO = {
    '说不出话': r'说不出话', '说不出': r'说不出(?!话)', '说不清': r'说不清',
    '说不出来的': r'说不出来的', '一句话也': r'一句话也(没|没有|不)',
    '沉默': r'沉默', '没说话': r'没(有)?说话', '没吭声': r'没吭声', '没吱声': r'没吱声',
    '涌上': r'涌上', '涌上心头': r'涌上心头', '五味杂陈': r'五味杂陈',
    '心里暖': r'心里(头)?暖', '踏实': r'踏实',
    '不安': r'不安', '慌': r'心(里|头)?发慌|慌得很|有点慌',
    '奇怪': r'奇怪', '不对劲': r'不对劲',
    '他知道': r'他知道', '他觉得': r'他觉得', '他明白': r'他明白',
    '安全感': r'安全感', '感觉很好': r'感觉很好|很舒服',
}
print()
print(f"{'情绪表达':<14}" + ''.join(f"{n:>12}" for n in DATA))
for k, pat in EMO.items():
    row = f"{k:<14}"
    for n, t in DATA.items():
        total = len(re.findall(r'[\u4e00-\u9fff]', t))
        c = len(re.findall(pat, t))
        dens = c / total * 10000 if total else 0.0
        row += f"{c:>6}({dens:>4.1f})"
    print(row)

# ── 2. 抽样真实例句：这些词在大师笔下长什么样 ──
def samples(text, pat, k=4, width=55):
    out = []
    ms = list(re.finditer(pat, text))
    random.shuffle(ms)
    for m in ms[:k]:
        s = max(0, m.start()-width)
        e = min(len(text), m.end()+width)
        frag = text[s:e].replace('\n', '¶')
        out.append(frag)
    return out

for probe, label in [
    (r'说不出话[来]?[。，、]', '说不出话'),
    (r'一句话也没(?:说|讲)', '一句话也没说'),
    (r'(?:心里|心头)(?:有种|有一种|一阵)[^。]{2,18}', '心里有种X（直给）'),
    (r'踏实', '踏实'),
    (r'沉默了?(?:一下|一会儿|片刻|很久)?', '沉默'),
]:
    print(f'\n──── 例句抽样：{label} ────')
    for n, t in DATA.items():
        for s in samples(t, probe, 2):
            print(f'[{n}] …{s}…')
