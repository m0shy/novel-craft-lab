# -*- coding: utf-8 -*-
"""第五轮·结构指纹扫描：三段列举、冒号警句、解释癖、缓冲词缺失

用法示例：python tools/analysis/scan-struct.py --lib ./corpus/
（--lib 为语料根目录，其下按《书名》子目录定位 txt；文件缺失按空文本计）
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

def build_targets(lib):
    return {
        '灵境': os.path.join(lib, '《灵境行者》', '灵境行者(1-500章).txt'),
        '主大纲': os.path.join(lib, '大纲优化_v21_人味修缮版.md'),
    }

def load(p):
    for enc in ('utf-8', 'gbk'):
        try:
            with open(p, encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError, OSError):
            continue
    return ''

PATTERNS = {
    '三段顿号列举(A、B、C)': r'[\u4e00-\u9fff]{2,6}、[\u4e00-\u9fff]{2,6}、[\u4e00-\u9fff]{2,6}',
    '冒号揭示(明白/知道/清楚/发现：)': r'(明白|知道|清楚|发现|意识到|意思是|意思是)[:：]',
    '解释癖(也就是说/换句话说/即)': r'(也就是说|换句话说|也就是说|所谓.{1,12}，是)',
    '因为…所以…': r'因为[^。]{2,20}所以',
    '之所以…是因为': r'之所以[^。]{2,30}是因为',
    '其实': r'其实',
    '毕竟': r'毕竟',
    '好像': r'好像',
    '有点/有些': r'有点|有些',
    '然后': r'然后',
    '就': r'就',
    '顿号总数': r'、',
    '分号总数': r'；',
    '省略号': r'……',
    '问号': r'？',
}

def main():
    ap = argparse.ArgumentParser(description='结构指纹扫描：三段列举/冒号警句/解释癖/缓冲词缺失')
    ap.add_argument('--lib', default='./corpus/', help='语料根目录（其下按《书名》子目录组织）')
    args = ap.parse_args()
    targets = build_targets(args.lib)

    data = {}
    for name, p in targets.items():
        t = load(p)
        n = len(re.findall(r'[\u4e00-\u9fff]', t))
        data[name] = (n, {k: len(re.findall(v, t)) for k, v in PATTERNS.items()})

    print(f"{'模式':<24}" + ''.join(f"{name:>14}" for name in targets))
    for k in PATTERNS:
        row = f"{k:<24}"
        for name in targets:
            n, c = data[name]
            dens = c[k] / n * 10000 if n else 0.0
            row += f"{c[k]:>8}({dens:>5.1f})"
        print(row)

    # 段落长度分布
    print()
    print("=== 段落统计 ===")
    for name, p in targets.items():
        t = load(p)
        paras = [x.strip() for x in t.split('\n') if len(re.findall(r'[\u4e00-\u9fff]', x)) > 0]
        if not paras:
            print(f"{name:<8} （无文本，跳过段落统计）")
            continue
        plens = [len(re.findall(r'[\u4e00-\u9fff]', x)) for x in paras]
        one_sent = sum(1 for x in paras if x.count('。') <= 1) / len(paras) * 100
        print(f"{name:<8} 段落数{len(paras)} 段均{statistics.mean(plens):5.1f}字 单句段占比{one_sent:5.1f}%")

if __name__ == '__main__':
    main()
