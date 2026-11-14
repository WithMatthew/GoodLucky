# W07D02真实净值教学样本

核验及获取日期：2026-11-08。用户已明确委托筛选免费、无需账户的公开教学样本。

## 来源与范围

- 标的：SPY，State Street SPDR S&P 500 ETF Trust；选择用于读取、日期和数据口径教学，不作买入建议，也不自动确定后续策略池。
- 来源：[发行人官方产品页](https://www.ssga.com/us/en/institutional/etfs/state-street-spdr-sp-500-etf-trust-spy)的“Most Recent NAV / NAV History”公开下载链接。
- 原文件URL：<https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-spy.xlsx>。
- 获取情况：无需登录、API密钥或付款，已成功下载278814字节。按用户的数据同步要求，现有.gitignore已显式放行本次原始快照、衍生CSV和元数据，可通过普通git add纳入版本管理；不推定免费公开下载意味着获得再分发许可。
- 原始文件：`data/raw/ssga/spy_nav_2026-11-08.xlsx`，未编辑；文件下载完成后的修改时间为2026-11-08T13:22:36.034458+00:00（北京时间21:22:36）。此为获取时间记录，不是行情发生或发布时点。
- SHA-256：`7aa8414e1cc8ab09f1fe20c321f5c87493c81b32936154f80db40b350286a683`。以本地快照和校验值固定版本；官方同一URL未来可能更新。
- 预先固定课堂窗口：2024-01-02至2024-01-08，按短时间窗口选择，非按表现筛选。从navhist工作表A715:B719提取五行，原顺序为日期倒序。
- 衍生CSV：`data/derived/spy_nav_2024-01-02_2024-01-08.csv`。来源日期文字转换为YYYY-MM-DD，NAV数值文本保留来源精度，额外记录原工作表行号；保留来源行序，不自动去重、填值或插行。
- 元数据：同目录同名`.metadata.json`，保存来源、原始及衍生校验值、提取时间、Python版本、源行号和处理规则。

## 字段与使用边界

| 字段 | 含义 | 单位与类型 |
| --- | --- | --- |
| date | 来源Date所标净值日期 | CSV文本YYYY-MM-DD，读取后为Python date |
| nav | 来源NAV，每份基金净资产价值 | 美元/份；CSV文本，读取后为float，空白保留为None |
| source_row | 原始navhist工作表行号 | 整数；排序后保持随同一条记录移动 |

这是发行人发布的每日每份净值，不是交易所close、盘中可成交报价或含分红再投资的总回报指数。每份NAV为（基金资产减负债）除以份额；市场买卖价格可以不同。程序没有实施前复权、后复权或分红再投资，也不能仅凭此表推定某段没有分红。来源字段为日期，不带时分秒或时区；课堂按发行人美国业务净值日期使用。W07D04补核了估值日规则，见下方；历史实际发布延迟及修订时间仍未知，不能用于模拟当时何时可获知数据。

频率为来源日频，仅有Date/NAV，没有OHLCV完整行情。W07D02时样本已有五行均能解析，未发现重复日期或空白NAV，但当时未独立校验预期交易日集合。W07D04已完成这个五行窗口的日期检查，见下方；历史W07D02“尚未检查”的记录保留，不能用“无空白”单独证明没有缺整行。

原始文件包含更长历史，工具为辨认布局曾显示首页近期数据；课堂只列上述窗口，没有绘图或评估策略。已查看的样本和近期字段不得作为全新未见数据。本份NAV快照不是最终测试集；W07D04后来另为用户指定的SPY、DIA、QQQ确定并保存了[正式研究快照及封存记录](etf-research-v1.md)，不与本样本混用。

## 复现与已执行验证

本轮实际`python`为3.14.6；历史W07D01记录为3.11.9，保留历史事实。新增脚本只依赖标准库，未安装第三方依赖；不把3.11.9写成本轮实测环境。

在仓库根目录执行：

```powershell
python -X utf8 -B src/prepare_spy_nav_sample.py
python -X utf8 -B src/read_nav_sample.py
python -X utf8 -B -m unittest discover -s tests -p test_nav_sample.py -v
```

第一步需要本地原始快照；只适配已核验的navhist布局，遇格式变化报错，不是通用XLSX解析器。读取日期区后，已核验的品牌更名说明作为数据区结束标记。第二步只读本地CSV，不联网或写入；对不存在日期、非YYYY-MM-DD格式及非有限/非正NAV报错，对空白保留None，对重复日期报告数量而不替用户选择真值。未实现交易日历或收益计算。

已执行：提取5行，原始文件哈希前后相同；日期升序输出01-02/03/04/05/08，无重复日期和空白净值。5项确定测试通过：排序/缺值/原输入保持、非法日期与格式拒绝、周末日期仍可解析、完全重复和冲突均报告且不删除、非有限或非正净值拒绝。

需要重新获取时，从上述官方链接另存新快照，不覆盖本次快照。来源URL可按官方页重新核验；不同快照结果及SHA-256可能不同。本次原始快照、衍生CSV和元数据已在.gitignore中放行，提交并推送后即可随仓库在设备间同步；具体命令见[仓库说明](../../README.md#数据的-git-追踪与-github-同步)。新增快照仍需单独添加放行规则，并记录对应版本。

技术参考：[Python date.fromisoformat](https://docs.python.org/3.11/library/datetime.html#datetime.date.fromisoformat)，2026-11-08核验其日期转换与有效性约束；项目函数额外要求规范YYYY-MM-DD。Python date本身不判断交易所是否开市。

## W07D04补充：日期完整性核验（2026-11-14）

[SPY 2023年招募说明书](https://www.sec.gov/Archives/edgar/data/884394/000119312523017928/d449477d497.htm)在样本期之前发布：Business Day依NYSE开市日定义，每个Business Day在Evaluation Time计算净值，估值参照NYSE常规交易收市，通常为纽约时间16:00。这里核实估值参照，不把它等同于公众实际收到该数值的时刻。

[NYSE公布的2024年日历](https://ir.theice.com/press/news-details/2023/NYSE-Group-Announces-2024-2025-and-2026-Holiday-and-Early-Closings-Calendar/default.aspx)与上述基金规则合用，2024-01-02至01-08预期五个净值日期为02、03、04、05、08；06/07为周末，不要求有记录。程序将这个独立生成的日期集合与实际集合逐项比较，不仅比较总行数。

[检查报告](../../reports/spy-nav-quality-2026-11-14.json)：预期5行、实际5个不同日期，缺日期0、多余日期0、重复日期0、缺NAV0。内存中排序，没有填补或删除来源记录；原始XLSX和CSV的SHA-256均与既有元数据相符。这只验证所列五行窗口和所列规则，不推广为整份多年NAV文件完整、值值准确或可交易。

复现：`python -X utf8 -B -m src.check_data_quality`，默认仅检查本教学样本；实际使用Python3.12.14，没有覆盖原始数据或改写2026-11-08元数据。旧`read_nav_sample.py`仍只做原来的读取检查，所以它打印“calendar not checked”是那个旧脚本的功能边界，不覆盖本次新增检查结果。
