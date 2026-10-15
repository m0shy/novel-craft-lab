# -*- coding: utf-8 -*-
"""
《玩家凶猛》风格蒸馏 · 全本量化统计
四层：基础 / 句法 / 词汇 / 对话叙事，另加无限流·沙雕·恐怖专项词频
输出 JSON 供后续报告使用

用法示例：python distill-pipeline.py --lib ./corpus/ --out stats.json
（--lib 为语料根目录，其下按 《玩家凶猛》/玩家凶猛.txt 组织语料）
"""
import argparse
import re, json, sys
from collections import Counter
from pathlib import Path

FILES = ["玩家凶猛.txt"]

STOPWORDS = set("""
的 了 是 在 我 你 他 她 它 们 有 和 就 都 而 及 与 着 或 一个 没有 我们 你们 他们 她们 自己 这个 那个 这些 那些 什么 怎么 这样 那样 这 那 也 又 还 但 不 没 很 太 更 最 只 被 把 让 给 对 从 向 到 上 下 里 外 中 内 一 二 三 四 五 六 七 八 九 十 百 千 万 亿 两 几 多 少 会 能 要 想 说 道 问 答 看 见 听 来 去 走 出 进 过 起 起来 下去 出来 进去 过来 过去 因为 所以 但是 然后 如果 虽然 可是 不过 只是 还是 或者 于是 便 便说 说道 说话 时候 现在 已经 正在 刚刚 忽然 突然 顿时 立刻 马上 一会儿 一下 这样 那样 这个 那个 这里 那里 今天 明天 昨天 东西 事情 地方 时间 之后 之前 以后 以前 之 其 此 彼 各 每 另 某 些 谁 哪 怎么 怎样 为何 何 如 同 连 按 沿 往 朝 为了 关于 对于 以及 等等 的话 一样 一般 似乎 好像 仿佛 像 如同 犹如 似的 显得 感觉 觉得 认为 知道 明白 想要 可以 应该 必须 需要 能够 比如 例如 包括 尤其 特别 非常 十分 相当 比较 稍微 略微 几乎 差点 简直 竟然 居然 究竟 到底 毕竟 反正 总之 因此 于是 接着
""".split())

TONE_WORDS = "呢 吧 吗 啊 啦 哦 嘛 呀 么 咯 哈 嘿 嗯 唔 呃 唉 嗨 哟 咧 呗 呐 嚓"
SPOKEN_WORDS = "卧槽 尼玛 操 特么 妈的 靠 我去 艹 你妹 妹的 他妈的 干 靠北 卧槽 我靠 你大爷 奶奶个 狗日的 妈蛋 沙雕 傻逼 逗比 二货 智障 扯淡 蛋疼 坑爹 作死 拉倒 得嘞 甭 咋 咋地 忒 贼 瞅 整 唠 嗑 妥 溜 浪 怂 拽 蔫 崩 叮 咣 咚 啪 砰 嗖 唰 咔 咯噔 咕噜 呼哧 哧 咝 嗬 嗷 呜 喵 汪 离谱 稳了 秒懂 逼格 内卷 凡尔赛 嘴强王者 狗带 韭菜 老铁 好家伙 铁子 批话 完事儿 嗷 整活 骚话 乐子人"

SENSE_WORDS = {
    "视觉": "看 望 瞧 瞅 盯 瞄 瞥 扫 视 打量 端详 凝视 眺望 注视 眯 睁 眨 盯 眼眶 瞳孔",
    "听觉": "听 闻 耳 声 响 鸣 轰 咚 咔 啪 砰 咣 嗡 轰隆 咯吱 沙沙 呼呼 哗啦 滴答 呜咽 尖叫",
    "嗅觉": "闻 嗅 香 臭 腥 臊 刺鼻 腥臭 芬芳 清香 腐臭 酸腐 尸臭",
    "味觉": "尝 甜 苦 辣 酸 咸 涩 鲜 麻 腻 腥 咸 铁腥",
    "触觉": "摸 触 碰 抚 抓 捏 按 揉 掐 冷 热 烫 凉 冰 痛 痒 麻 酥 软 硬 湿 干 滑 黏 刺痛",
}

# ---- 玩家凶猛专项词频 ----
SPECIAL = {
    "游戏系统词": "玩家 杀场 地球杀场 副本 剧本任务 系统 装备 物品栏 经验 等级 品质 稀有 神话 技能 称号 任务 奖励 惩罚 传送 星门 游戏 面板 引导 新手 超凡 异能 神力 神格 造物主",
    "推理科学词": "推理 分析 推断 可能 逻辑 实验 测试 概率 数据 化学 物理 生物 基因 反应 结论 假设 排除 验证 计算 测量 观察 原理 结构 频率 强度 比例",
    "沙雕骚话词": "吐槽 骚话 卧槽 草 靠 蛋疼 二货 智障 沙雕 逗比 扯淡 离谱 稳了 好家伙 铁子 批话 完事儿 整活 乐子人 神经病 精神病 脑残 二 傻子 智熄",
    "恐怖灵异词": "鬼 尸体 血 尸斑 人脸 怪谈 灵异 惨叫 阴森 鬼打墙 怨 腐烂 腐臭 尸块 人面 怪物 怪猫 眼球 白骨 尸骨 阴风 寒气 惊悚 恐怖 瘆人 头皮发麻",
    "战斗词": "轰 炸 爆 斩 拳 踹 砸 撞 撕 咬 虫群 枪 剑 刀 炮 机甲 战舰 自爆 焚 燃 毁灭 湮灭 重创",
    "人物名": "李昂 王丛珊 柴柴 柴翠翘 素霓笙 米迦勒 丁真嗣 霍恩海姆 邢河愁 竺学民 石青松",
}

def load_chapters(base):
    text = ""
    for f in FILES:
        text += (base / f).read_text(encoding="utf-8", errors="ignore") + "\n"
    chapters = []
    cur_title, cur_lines = None, []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        m = re.match(r'^第\s*[一二三四五六七八九十百千零\d]+\s*章\s*(.+)$', line)
        if m and len(line) < 40:
            if cur_title is not None:
                chapters.append((cur_title, "\n".join(cur_lines)))
            cur_title, cur_lines = line, []
        else:
            if cur_title is None and not cur_lines:
                if line.startswith("《") and "作者" not in line and line.endswith("》"):
                    continue
                if line.startswith("作者") or line.startswith("来源") or line.startswith("网址"):
                    continue
                if line.startswith("内容简介") or line.startswith("后记"):
                    continue
            cur_lines.append(line)
    if cur_title is not None:
        chapters.append((cur_title, "\n".join(cur_lines)))
    return chapters

def split_sentences(text):
    sents = []
    buf = ""
    for ch in text:
        buf += ch
        if ch in "。！？!?…":
            sents.append(buf)
            buf = ""
    if buf.strip():
        sents.append(buf)
    return sents

def count_chars(s, with_punct=True):
    if with_punct:
        return len(s)
    return len(re.sub(r'[\s\u3000，。！？、；：“”‘’（）《》【】…—\-·,\.!\?;:()\[\]<>]', '', s))

def main():
    ap = argparse.ArgumentParser(description='《玩家凶猛》全本量化统计，输出 JSON 供蒸馏报告使用')
    ap.add_argument('--lib', default='./corpus/', help='语料根目录（其下按 《玩家凶猛》/玩家凶猛.txt 组织）')
    ap.add_argument('--out', default='stats.json', help='统计结果 JSON 输出路径')
    args = ap.parse_args()

    base = Path(args.lib) / '《玩家凶猛》'
    missing = [f for f in FILES if not (base / f).is_file()]
    if missing:
        print('未找到语料：' + '、'.join(str(base / f) for f in missing))
        print('请将语料放入 --lib 指定的目录（结构：《玩家凶猛》/玩家凶猛.txt）')
        sys.exit(4)

    out = Path(args.out)
    chapters = load_chapters(base)
    bodies = [b for _, b in chapters]
    full = "\n".join(bodies)

    total_chars_punct = count_chars(full, True)
    total_chars_clean = count_chars(full, False)
    chapter_lens = [count_chars(b, False) for b in bodies]

    paras = [p.strip() for p in full.split("\n") if p.strip()]
    para_lens = [count_chars(p, False) for p in paras]

    all_sents = [s for s in split_sentences(full) if s.strip()]
    sent_lens = [count_chars(s, False) for s in all_sents]
    sent_lens = [l for l in sent_lens if l > 0]

    exclaim = sum(1 for s in all_sents if s.strip().endswith("！") or s.strip().endswith("!"))
    question = sum(1 for s in all_sents if s.strip().endswith("？") or s.strip().endswith("?"))
    ellipsis = sum(1 for s in all_sents if "…" in s or "..." in s)
    declar = len(all_sents) - exclaim - question

    try:
        import jieba
        words = [w for w in jieba.cut(full) if w.strip() and len(w.strip()) >= 1]
        words_nostop = [w for w in words if w not in STOPWORDS and re.search(r'[\u4e00-\u9fff]', w)]
        wc = Counter(words_nostop)
        top_words = wc.most_common(300)
    except Exception as e:
        top_words = []
        print("jieba failed:", e)

    tone_counter = Counter()
    for w in TONE_WORDS.split():
        tone_counter[w] = full.count(w)

    spoken_counter = Counter()
    for w in SPOKEN_WORDS.split():
        c = full.count(w)
        if c > 0:
            spoken_counter[w] = c

    sense_counter = {}
    for k, ws in SENSE_WORDS.items():
        c = Counter()
        for w in ws.split():
            c[w] = full.count(w)
        sense_counter[k] = dict(c.most_common(20))

    special_counter = {}
    for k, ws in SPECIAL.items():
        c = Counter()
        for w in ws.split():
            c[w] = full.count(w)
        special_counter[k] = dict(c.most_common(50))

    # 对话引导词
    guide_words = ["道", "说", "问", "笑", "说道", "笑道", "问道", "淡淡道", "沉声道", "沉声", "低声", "冷冷道", "缓缓道", "怒道", "大声道", "朗声道", "哼道", "呵道", "呐喊道", "答道", "回答", "开口", "嘀咕", "吐槽", "嘀咕道", "随口道", "随意道", "平静道", "缓缓道"]
    guide_counter = {w: full.count(w) for w in guide_words}

    # 微反应词
    micro_words = "一愣 冷笑 耸肩 皱了皱眉 一顿 咧嘴 一僵 苦笑 笑眯眯 眯起眼 撇嘴 挑眉 一滞 翻白眼 脸色微变 目光一凝 瞳孔一缩 心头一凛 倒吸一口凉气 眼角一抽 眼角抽了抽 眼睛一横 撇了撇嘴 眉头微皱 眉头一挑 一挑眉梢 头皮发麻 打了个寒颤 鸡皮疙瘩"
    micro_counter = Counter()
    for w in micro_words.split():
        c = full.count(w)
        if c > 0:
            micro_counter[w] = c

    # 拟声词
    onomatopoeia = "轰 砰 啪 咚 咔嚓 咔嚓嚓 呲 嗖 唰 咔 咯噔 咕噜 呼哧 滴答 沙沙 呼呼 哗啦 咣 嗡 嗤 嘶 嗷 喵 汪 咯咯 嗬嗬 呜呜 哇哇 啊啊"
    onoma_counter = Counter()
    for w in onomatopoeia.split():
        c = full.count(w)
        if c > 0:
            onoma_counter[w] = c

    dialog_pairs = re.findall(r'“([^”]{1,200})”', full)
    dialog_text = "".join(dialog_pairs)
    dialog_chars = count_chars(dialog_text, False)
    dialog_ratio = dialog_chars / total_chars_clean if total_chars_clean else 0
    dialog_lens = [count_chars(d, False) for d in dialog_pairs]

    think_patterns = ["心想", "暗想", "心道", "心说", "心里", "暗自", "暗忖", "腹诽", "默念", "心念", "念头", "心里咯噔", "念头", "嘀咕"]
    think_counter = {p: full.count(p) for p in think_patterns}

    # 系统面板格式【】
    sys_panel = len(re.findall(r'【[^】]{1,60}】', full))
    colon_speech = len(re.findall(r'[：:]\s*“', full))

    def stats(nums):
        if not nums:
            return {}
        n = len(nums)
        mean = sum(nums) / n
        var = sum((x - mean) ** 2 for x in nums) / n
        import math
        sd = math.sqrt(var)
        cv = sd / mean if mean else 0
        sorted_nums = sorted(nums)
        def q(p):
            k = (n - 1) * p
            f = int(k)
            c = k - f
            if f + 1 < n:
                return sorted_nums[f] * (1 - c) + sorted_nums[f + 1] * c
            return sorted_nums[f]
        return {
            "count": n, "mean": round(mean, 2), "sd": round(sd, 2), "cv": round(cv, 4),
            "min": sorted_nums[0], "max": sorted_nums[-1],
            "p25": round(q(0.25), 1), "p50": round(q(0.5), 1), "p75": round(q(0.75), 1),
            "p90": round(q(0.9), 1), "p99": round(q(0.99), 1),
        }

    def bucket(nums):
        bins = {"1-5":0,"6-10":0,"11-15":0,"16-20":0,"21-30":0,"31-50":0,"51-100":0,"101+":0}
        for x in nums:
            if x<=5: bins["1-5"]+=1
            elif x<=10: bins["6-10"]+=1
            elif x<=15: bins["11-15"]+=1
            elif x<=20: bins["16-20"]+=1
            elif x<=30: bins["21-30"]+=1
            elif x<=50: bins["31-50"]+=1
            elif x<=100: bins["51-100"]+=1
            else: bins["101+"]+=1
        total = len(nums) or 1
        return {k: round(v/total*100, 2) for k, v in bins.items()}

    result = {
        "基础": {
            "章节数": len(chapters),
            "总字数_含标点": total_chars_punct,
            "总字数_不含标点": total_chars_clean,
            "平均章字数": round(sum(chapter_lens)/len(chapter_lens), 0) if chapter_lens else 0,
            "章节字数分布": stats(chapter_lens),
            "段落总数": len(paras),
            "平均段字数": stats(para_lens),
        },
        "句法": {
            "句子总数": len(sent_lens),
            "平均句长": stats(sent_lens),
            "句长分布_百分比": bucket(sent_lens),
            "句式": {
                "陈述句": declar, "陈述占比": round(declar/len(all_sents)*100,1),
                "感叹句": exclaim, "感叹占比": round(exclaim/len(all_sents)*100,1),
                "疑问句": question, "疑问占比": round(question/len(all_sents)*100,1),
                "含省略号句": ellipsis, "省略占比": round(ellipsis/len(all_sents)*100,1),
            }
        },
        "词汇": {
            "高频词_top100": top_words[:100],
            "高频词_101_300": top_words[100:300],
            "语气词": dict(tone_counter.most_common(30)),
            "口语词": dict(spoken_counter.most_common(80)),
        },
        "玩家凶猛专项词频": special_counter,
        "对话叙事": {
            "对话引号对数": len(dialog_pairs),
            "对话字数": dialog_chars,
            "对话占比": round(dialog_ratio*100, 2),
            "对话长度分布": stats(dialog_lens),
            "冒号引语数": colon_speech,
            "心理独白标记": think_counter,
            "五感词频": sense_counter,
            "对话引导词": guide_counter,
            "微反应词": dict(micro_counter.most_common(40)),
            "拟声词": dict(onoma_counter.most_common(40)),
            "系统面板数": sys_panel,
        }
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("DONE. chapters=", len(chapters), "chars_clean=", total_chars_clean, "sents=", len(sent_lens), "out=", str(out))

if __name__ == "__main__":
    main()
