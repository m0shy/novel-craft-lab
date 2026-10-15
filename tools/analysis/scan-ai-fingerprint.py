# -*- coding: utf-8 -*-
"""第五轮去AI味·实证扫描：三书 vs 我方稿件的症状词密度 + 句长分布

用法示例：python tools/analysis/scan-ai-fingerprint.py --lib ./corpus/
（--lib 为语料根目录，其下按《书名》子目录定位 txt；文件缺失自动跳过）
"""
import argparse
import os
import re
import statistics
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PATTERNS = {
    '然而': r'然而',
    '此外': r'此外',
    '与此同时': r'与此同时',
    '不仅…': r'不仅',
    '值得注意的是': r'值得注意的是',
    '这意味着': r'这意味着',
    '本质上': r'本质上',
    '归根结底': r'归根结底',
    '涌上心头': r'涌上心头',
    '心中一凛': r'心中一凛',
    '五味杂陈': r'五味杂陈',
    '说不出话': r'说不出话',
    '说不清': r'说不清',
    '某种难以': r'某种难以',
    '仿佛': r'仿佛',
    '似乎': r'似乎',
    '显然': r'显然',
    '终于明白': r'终于明白',
    '从这天起': r'从这天(起|开始)',
    '真正的': r'真正的',
    '从来不是': r'从来不是',
    '从来都不是': r'从来都不是',
}

def build_files(lib):
    return {
        '灵境行者': [os.path.join(lib, '《灵境行者》', '灵境行者(1-500章).txt'),
                   os.path.join(lib, '《灵境行者》', '灵境行者(501-1000章).txt')],
        '大奉打更人': [os.path.join(lib, '《大奉打更人》', '_全本合并.txt')],
        '玩家凶猛': [os.path.join(lib, '《玩家凶猛》', '玩家凶猛.txt')],
        '主大纲v21': [os.path.join(lib, '大纲优化_v21_人味修缮版.md')],
    }

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
        except FileNotFoundError:
            pass
    return text

def sentence_lengths(text):
    # split on 。！？； and newlines, count CJK chars per sentence
    parts = re.split(r'[。！？；\n]', text)
    lens = [len(re.findall(r'[\u4e00-\u9fff]', s)) for s in parts]
    lens = [x for x in lens if x > 0]
    return lens

def main():
    ap = argparse.ArgumentParser(description='症状词密度 + 句长分布扫描（对照语料 vs 我方稿件）')
    ap.add_argument('--lib', default='./corpus/', help='语料根目录（其下按《书名》子目录组织）')
    args = ap.parse_args()
    FILES = build_files(args.lib)

    results = {}
    for name, paths in FILES.items():
        t = load(paths)
        n = len(re.findall(r'[\u4e00-\u9fff]', t))
        counts = {k: len(re.findall(v, t)) for k, v in PATTERNS.items()}
        lens = sentence_lengths(t)
        results[name] = (n, counts, lens)

    print(f"{'词':<12}" + ''.join(f"{name:>12}" for name in FILES))
    print(f"{'总字数':<12}" + ''.join(f"{results[n][0]:>12,}" for n in FILES))
    for k in PATTERNS:
        row = f"{k:<12}"
        for n in FILES:
            total, counts, _ = results[n]
            dens = counts[k] / total * 10000 if total else 0.0
            row += f"{counts[k]:>6}/{dens:>4.1f}"
        print(row)

    print()
    print("=== 句长分布（中文字符/句） ===")
    for n in FILES:
        lens = results[n][2]
        if not lens: continue
        mean = statistics.mean(lens)
        med = statistics.median(lens)
        sd = statistics.pstdev(lens)
        short = sum(1 for x in lens if x <= 5) / len(lens) * 100
        long_ = sum(1 for x in lens if x >= 40) / len(lens) * 100
        print(f"{n:<10} 均值{mean:5.1f} 中位{med:5.1f} 标准差{sd:5.1f} 短句≤5字占比{short:4.1f}% 长句≥40字占比{long_:4.1f}%")

if __name__ == '__main__':
    main()
