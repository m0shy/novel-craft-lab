# novel-craft-lab

[![CI](https://github.com/m0shy/novel-craft-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/m0shy/novel-craft-lab/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[简体中文](README.md) · [English](README_ENG.md)

AI 辅助网文创作的**方法论实验库**：怎么用"人在环"的方式和模型一起写小说——章生产线 SOP、可脚本化的质检工具链、以及对公开作家作品的文风蒸馏全记录。

> 本仓库只发布方法论与工具。自创小说的正文、大纲与设定**不随仓库发布**；蒸馏对象语料同样不在仓库内。

## 方法论（methodology/）

| 文档 | 内容 |
|---|---|
| `chapter-pipeline-sop.md` | 章生产线最终形态：六步流程，人机各归其位 |
| `danger-checklist-and-gated-workflow.md` | 50 条 AI 写作危险清单 × G0–G6 每章拦截关卡（全库总纲） |
| `writing-calibration.md` | 写作口径三层互证：语录层 × 语料实证层 × 平台时效层 |
| `paired-analysis.md` | "新人该学成名前还是成名后"：同作者 16 部作品配对实证 |
| `case-study-lingjing-opening.md` | 一个完整的开篇对标分析案例 |

## 质检工具（tools/）

- `qa/qc-script.py` —— 红线词表落地扫描器
- `qa/redline-wordlist.md` —— AI 指纹词 / 情绪直陈 / 句式惯性 / 平台红线 词表
- `qa/style-conventions.md` —— 体例规范（格式/标点/数字/段落）
- `analysis/` —— AI 指纹密度、结构指纹、情绪词频三个扫描器
- `preference-samples.md` —— 偏好样本库模板（DPO/FTPO 数据从 0 到 1 的起点）

## 文风蒸馏（style-distillation/）

两位公开作家、三部作品各自七轮蒸馏的终版：每部一份 `SKILL.md`（规则产物）+ `final-report.md`（方法论复盘），以及可复用的统计流水线脚本。**不含任何原文语料**；规则文档中存在少量短句引用，仅作分析示例。

## 经验：为什么这个库一半是"失败记录"

1. **工具打磨 ≠ 闭环验证**：三套文风 skill 各迭代七版（全本词频 + 分层采样精读），复盘发现它们从未真正进入生产链路——先跑通最小闭环，再打磨工具。
2. **没有反馈数据的迭代是空转**：偏好样本库长期停留在模板 + 0 条数据，风格方向无法量化校准。
3. **AI 初稿禁止直接发布**是铁律：发布前必过人工修缮 + 脚本质检双重关。
4. **质检必须可脚本化**：红线词、AI 指纹、结构惯性都能变成确定性检查，比"感觉不行"可靠。
5. **平台合规先于一切**：各平台对 AI 辅助创作的标注与占比要求持续收紧，批量生成路线不可持续。

## License

代码与工具 MIT；蒸馏文档为分析性产物，仅含统计结论与带章号的原文风格示例（各SKILL约二十则，合计约万字，作为蒸馏分析样例保留，仅限研究用途）。
