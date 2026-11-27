# 结业后进阶路线：ML 多因子与职业量化（草案）

2026-11-27 起草，W24 结业答辩时按实际能力与个人目标修订定稿。本文是规划，不是课程进度；不计课次。

## 三条目标路径

| 路径 | 终点能力 | W24 之后的追加投入（约） | 主要门槛 |
| --- | --- | --- | --- |
| A. 个人系统化投资者 | 小资金运行低频 ETF 规则组合 | 3–6 个月：小额实盘试运行（另行授权） | 账户、税务、资金上限与停用规则 |
| B. ML 多因子研究者 | 独立完成个股截面因子与 ML 选股研究，可做模拟或小额实盘 | 约 150–250 小时（每周 5 小时约 7–12 个月） | **时点可得（PIT）的个股数据**、组合优化、风险模型 |
| C. 职业量化入行 | 能通过量化研究员、量化开发或风控岗位的面试与试用 | 约 400–700 小时（每周 5 小时约 1.5–2.5 年；每周 12–15 小时约 9–12 个月） | 数学/统计功底、实证作品集；买方研究岗通常要求理工科硕士或博士 |

路径 B 和 C 的模块有重叠。C 等于 B 加上 P1 的深化、P6 和面试准备。

## 模块与周期（按每周 5 小时估算）

| 编号 | 模块 | 周数 | 核心内容 | 代表资料（开课前核对版本） |
| --- | --- | --- | --- | --- |
| P1 | 数学、统计与计量补强 | 8–10 | 线性代数与概率复习；回归推断（OLS 假设、Newey-West 稳健标准误）；时间序列（平稳性、AR、GARCH）；多重检验 | Wooldridge《Introductory Econometrics》；Tsay《Analysis of Financial Time Series》；ISLP（ISL 的 Python 版） |
| P2 | 实证资产定价与因子 | 8–10 | CAPM、Fama-French 3/5 因子、动量；组合排序与 Fama-MacBeth；用公开数据复现 3–5 个因子；因子复现危机 | Bali-Engle-Murray《Empirical Asset Pricing》；Open Source Asset Pricing（Chen-Zimmermann）；JKP 全球因子库；Ken French 数据库 |
| P3 | 组合构建与风险模型 | 8–10 | 均值方差与其不稳定性；Black-Litterman；风险平价；协方差收缩；Barra 式多因子风险模型；带换手与成本约束的优化（cvxpy） | Grinold-Kahn《Active Portfolio Management》；Ang《Asset Management》 |
| P4 | 金融机器学习深化 | 10–12 | 标签设计、元标签（meta-labeling）、CPCV 组合清洗交叉验证；复现 Gu-Kelly-Xiu；集成学习与神经网络基础（PyTorch）；模型衰减监控 | López de Prado《Advances in Financial Machine Learning》；Kelly-Xiu《Financial Machine Learning》综述（2023） |
| P5 | 数据与工程 | 6–8 | PIT 数据源选择与入库（Parquet/DuckDB）；日更管道与监控；实盘执行接口与对账；回测框架交叉验证 | 按所选市场的数据商官方文档 |
| P6 | 微结构、执行与衍生品（职业路径） | 8–10 | 订单簿与冲击成本；Almgren-Chriss 执行；期权定价与希腊字母基础 | Harris《Trading and Exchanges》；Hull《Options, Futures, and Other Derivatives》 |
| P7 | 作品集与求职（职业路径） | 持续 | 3 份可复现研究报告（含失败结论）；Numerai 或 Kaggle 金融竞赛；概率、统计与编程面试题 | 公开竞赛平台；面试题集 |

- **路径 B 的顺序**：P2 → P3（精简）→ P4 → P5，P1 按需穿插。
- **路径 C 的顺序**：P1 → P2 → P3 → P4 → P5 → P6，P7 从 P2 起持续进行。

## 需要用户决策的事项

1. **目标市场**：继续做美股，还是转向 A 股？
   - A 股个人可获得的 PIT 基本面数据更多（如 Tushare Pro、聚宽、米筐），ML 选股更容易实际落地；但规则不同：T+1、涨跌停、印花税、融券受限。
   - 美股免费的 PIT 个股数据很少，常见的是付费数据（如 Sharadar）或学术渠道（WRDS）。
2. **目标路径**：选 A、B 还是 C，以及每周投入的时间。这决定上表的周期。
3. **实盘**：任何真实资金操作都须另行显式授权，见 AGENTS.md。
