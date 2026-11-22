# 官方Python材料、数据与依赖核查

核查日期：2026-10-24。性质：初始化阶段的静态审查，不是第一周学习验收，也不是代码可运行性验证。

## 官方入口与审查范围

作者Guillaume Coqueret与Tony Guida的[官方Python索引](https://www.mlfactor.com/python.html)列出按章节组织的官方notebooks，也单独列出第三方实现。本项目优先采用前者。[官网前言](https://www.mlfactor.com/index.html)指向作者的[材料仓库](https://github.com/shokru/mlfactor.github.io/tree/master/material)。Python版书籍信息可核对[出版社页面](https://www.routledge.com/Machine-Learning-for-Factor-Investing-Python-Version/Coqueret-Guida/p/book/9781003121596)。

本轮审查的是官网及仓库中发布的Python代码文本，并未逐页比对出版版书籍，因此不声称与纸书所有内容完全一致。官方索引所称notebooks目前在所查仓库以HTML页面提供；递归目录检查未找到.ipynb文件。

| 项目 | 核查结果 |
| --- | --- |
| 官方仓库 | shokru/mlfactor.github.io，默认分支master |
| 本轮固定参考提交 | 572b22acd4dbf58ef9a6dadbdcd976344d3af1d4 |
| 该提交日期 | 2023-07-17，来自仓库元数据；不是本轮核查日期 |
| 目录审查 | 检查递归文件列表；未完整克隆仓库 |
| 代码审查 | 阅读第1、4、5、10、12章的部分Python代码块、导入项与关键数据处理逻辑；没有执行官方实验 |
| 数据操作 | 仅查看入口、描述和文件元数据；未下载或读取原始数据二进制文件 |

固定提交用于后续追溯，不代表其依赖仍可直接安装或所有示例都能在当前Python运行。

## 数据入口、格式缺口与使用条件

[官方Python第1章](https://www.mlfactor.com/material/CHAPTER_1.html)读取本地data_ml.csv，但在上述提交的递归目录中未找到该文件。仓库提供以下入口：

| 入口 | 本轮观察 | 尚待核实 |
| --- | --- | --- |
| [material/data_ml.RData](https://github.com/shokru/mlfactor.github.io/blob/572b22acd4dbf58ef9a6dadbdcd976344d3af1d4/material/data_ml.RData) | 元数据大小22,812,797字节，约22.8MB；未下载 | 使用条件、实际字段、数据内容及Python读取兼容性 |
| [material/README.md](https://github.com/shokru/mlfactor.github.io/blob/572b22acd4dbf58ef9a6dadbdcd976344d3af1d4/material/README.md)中的Excel入口 | 作者README链接至[Google Drive文件](https://drive.google.com/file/d/17wm7QOqy90s7Jy-v1ZEO-iOkZn4mdXP7/view?usp=sharing) | 访问可用性、大小、内容和格式；未下载验证 |
| 官方示例所用CSV | 代码明确引用本地文件 | 不能假设已有现成CSV；后续如转换必须保存转换步骤、列名和原始文件哈希 |

[官网数据说明](https://www.mlfactor.com/notdata.html)描述的样本覆盖1998年11月至2019年3月、1,207只美国上市股票及93个特征；示例另筛选2000–2018年。以上是作者描述，未由本地数据读取复核。该说明称特征已经按时点作横截面变换，未来收益字段包含分红；不能把变换后的特征值当作原始美元金额，也不能再次给总收益加分红。

后续至少核实以下字段语义：[字段说明入口](https://www.mlfactor.com/data-description.html)、股票标识、日期、Mom_11M_Usd、Vol1Y_Usd、Mkt_Cap_12M_Usd和R1M_Usd。未来1/3/6/12个月收益列属于标签候选，不能放入预测输入。

仓库元数据未标明项目许可证，本轮文件列表也未找到适用于整个项目的许可证；字体许可证不代表代码或金融数据许可。作者公开提供复现材料不等于可以任意再分发。第2周获取数据前查明适用的学习使用条件与来源；尚未确认的权限写为未知，不把“公开链接”写成“开放数据许可证”。本轮未复制、分发原始数据或整套官方代码。

特征的真实发布日期、是否使用修订后财报、退市收益与样本选择规则仍需核实。日期列和滞后一期本身都不能证明数据在历史当时实际可得。

## 代码静态检查与拟用依赖

| 官方材料 | 观察到的依赖或实现 | 对本项目的影响 |
| --- | --- | --- |
| [第1章](https://www.mlfactor.com/material/CHAPTER_1.html) | pandas、numpy、matplotlib；按列位置选特征，并存在按完整日期覆盖筛选股票的示例 | 后续改为按字段名选择；不照搬可能利用未来完整性的选样方式，记录偏离官方实现的理由 |
| [第4章](https://www.mlfactor.com/chap_4.html) | seaborn、statsmodels、IPython等 | 核心数据检查未必需要全部依赖；按所执行片段决定 |
| [第5章](https://www.mlfactor.com/chap_5.html) | scikit-learn的Lasso、Ridge、ElasticNet，依赖此前已定义的数据变量 | 先做简单线性模型；全样本拟合的教学图不能直接作为样本外验证证据 |
| [第10章](https://www.mlfactor.com/chap_10.html) | scikit-learn指标与GridSearchCV、skopt.BayesSearchCV | 按月份自定义时间顺序验证；本阶段不使用贝叶斯调参 |
| [第12章](https://www.mlfactor.com/chap_12.html) | xgboost、scipy、换手计算；存在缺失收益填0的片段 | 只提取所需方法并检查假设，不预装XGBoost，不默认缺失收益等于0 |

在所查递归目录中未找到requirements、pyproject、Python环境配置或Python锁定文件；仓库的renv.lock属于R环境，不能当作Python版本约束。这里只完成了静态依赖识别，未验证各章节的完整依赖闭包或运行兼容性。

最小环境候选为numpy、pandas、matplotlib、scikit-learn及其正常传递依赖。若选Excel或RData，只在确认兼容性后增加所需的openpyxl或pyreadr。statsmodels、seaborn、IPython和Jupyter按实际需求决定；前8周不要求深度学习框架、XGBoost或scikit-optimize。

第2周才选择合适的Python版本、创建独立环境、安装最小依赖并记录实际版本。优先用小脚本完成，不要求另购软件；不为照搬整本书提前安装全部工具。

## 本机只读检查

2026-10-24检查当前默认解释器及包元数据：

- 当前默认Python为3.14.6；启动器另外列出3.13和2.7。仅拟使用兼容的Python 3环境，不使用Python 2。
- 当前默认解释器未查到numpy、pandas、matplotlib、scikit-learn、scipy、statsmodels、seaborn、nbformat、jupyterlab、notebook和ipykernel的安装元数据。这不代表所有其他环境都没有这些包。
- 主线历史记录中的Python 3.11.9属于当时的验证证据，本轮不修改该记录，也不假定当前默认环境仍相同。
- 本轮未创建环境、安装软件、调整全局包或运行研究代码。所选依赖与当前解释器的兼容性留待环境建立时检查，不能把“静态读取成功”写成“实验可运行”。

## 后续核查入口

MLF-W01由用户理解资料来源与研究问题；MLF-W02再完成数据使用条件、格式转换、字段定义、可获得时点、依赖兼容性及小样本读取检查。只有实际取得证据后，才在[结论文件](conclusions.md)更新相应事实与限制。


## 课前书籍与目录复核（2026-11-15）

为回应用户对教学路径与书籍关系的提问，本轮重新读取作者[官方Python索引](https://www.mlfactor.com/python.html)和[前言](https://www.mlfactor.com/)。索引说明提供按章组织的官方Python材料，另列第三方实现；官网正文保留R版说明，因此课程引用官网章节时明确来源，不声称与Python纸本逐页一致。

官网目录可确认第1章数据、第3章因子、第4章预处理、第5章回归、第10章验证、第12章回测，以及树、神经网络、集成等更广主题。8周选读映射和用户代码分工是教师结合本地范围作出的教学设计，不是作者给出的课程安排。前言列出的数学/统计/金融前置知识将按需补讲。

原出版社ISBN/DOI路径本轮直开返回403；通过出版社域搜索查得[另一出版社书籍入口](https://www.routledge.com/Machine-Learning-for-Factor-Investing-Python-Version/Coqueret-Guida/p/book/9780367639723)，搜索摘要确认书名《Machine Learning for Factor Investing: Python Version》及作者Guillaume Coqueret、Tony Guida。此项为网页/搜索摘要核对，不是出版版全文阅读。

本轮未重新检查仓库提交或数据文件列表，未验证历史CSV缺口是否仍存在，未安装环境、下载研究数据或运行实验；此前数据/环境细节仍按2026-10-24的核查日期理解，W02实际使用前需更新核实。

## MLF-W01概念来源复核（2026-11-15）

正式开课前重新读取[官方Python索引](https://www.mlfactor.com/python.html)和[官网第3章3.2.2–3.2.3](https://www.mlfactor.com/factor.html)。后者说明按特征排序、分组、设置权重、观察随后收益，以及经典两端多空因子的构造。课堂区别特征/信号简称、组合与收益序列；主线资产定价模型公式未引入本课验收。

[第一课](lesson-01.md)中的3个月窗口、虚构股票、1,000美元和两组算例是教师设计，未将其等同于官方数据字段或实证发现。本轮仅浏览概念网页，未重新检查数据许可、仓库文件清单或环境，未下载数据、运行模型或接触封存数据。官方资料与问题卡环节将在A组反馈后继续讲解。

## MLF-W01资料环节复核（2026-11-15，A组反馈后）

再次读取[官方Python索引](https://www.mlfactor.com/python.html)、[Python第1章](https://www.mlfactor.com/material/CHAPTER_1.html)及[官网第1章](https://www.mlfactor.com/notdata.html)。核实网页列出官方/第三方材料的区别、月频股票数据说明、R1M_Usd为未来一个月含分红总收益、输入特征经过横截面变换，以及Python示例读取本地data_ml.csv。这是网页内容核查，不是原始数据验证或代码运行。

课堂将资料分为参考代码、作者数据说明和仍待本地核实的事项，举财报归属期早于实际发布日期的例子说明时点核查的用途。官方字段的单位/变换、实际可得时点、标签区间、来源使用条件、格式与运行环境仍待W02核实。未重查仓库目录，2026-10-24的CSV缺口保持其历史日期；未读取原始数据、下载文件或接触主线封存区间。

2026-11-15 B组反馈后的补讲复核：再次读取同一[官方Python第1章](https://www.mlfactor.com/material/CHAPTER_1.html)，核对输入特征已经均匀化的文字说明。为解释含义，课件用教师自定“升序名次/4”的虚构变换示范原始6%与排名0.75的区别；该公式不是已查明的官方实现。官方精确变换、并列处理及字段语义仍待W02核实，本轮没有下载原始数据或执行作者实验。

<a id="mlf-w02-materials"></a>
## MLF-W02 开课核查（2026-11-22）

作者将书中数据集提供给读者复现示范，并指向材料仓库。这个说明支持本地教学复现的用途。此次核对的是作者文字，尚待查明上游来源及进一步使用、再分发的条件。[作者前言](https://www.mlfactor.com/) · [第 1 章数据集说明](https://www.mlfactor.com/notdata.html#dataset) · [作者材料目录](https://github.com/shokru/mlfactor.github.io/tree/master/material)

| 作者字段 | 已从作者资料核对的含义 | 实际使用前还需核对 |
| --- | --- | --- |
| `stock_id`、`date` | 官方 Python 示例按股票标识和日期组织月度观察 | 文件内的日期类型、月末口径、相同股票同月行数 |
| `Mom_11M_Usd` | 美元计价的价格动量，窗口标为往前 12 个月至往前 1 个月。作者说明输入特征按当月股票横截面变换过，列值表达相对位置 | 开课时待核查变换。后续已确认核心公式，逐股价格端点、并列取整及实际交付仍待证据。[补讲核查](#mlf-w02-uniformization) |
| `R1M_Usd` | 对齐到当前行的随后一个月总收益，已包含期间分红。作为未来标签使用 | 原始文件的数值比例、区间端点和可得时间 |

字段原始定义与文件中数值所经历的变换应结合阅读。[作者字段表](https://www.mlfactor.com/data-description.html) · [官方 Python 第 1 章](https://www.mlfactor.com/material/CHAPTER_1.html)

读取作者原始文件前，沿用计划预登记**观察月份**：训练 2010-01 至 2013-12，验证 2014-01 至 2015-12，最终测试 2016-01 至 2018-12。同一个月的股票属于同一段。进入下一段前剔除收益期间越过分段边界的旧标签，拟合时只纳入当时已揭晓的标签。区间内实际能用哪些月份，待核对标签端点和可得时点后记录。查字段定义时，作者网页同页列有全样本标签的描述统计；本次未据此选字段或改划分。未读取作者原始样本或计算任一区间表现。

本机已建副线专用环境 `mlf_lesson_works/.venv`，Windows 64 位、Python 3.14.6，虚拟环境与基础解释器路径已核对为不同。本环节只需标准库 `csv` 和 `decimal`。教师读入[虚构教学 CSV](../../../data/synthetic/mlf_stock_month.csv) 共两行，验证甲的分数、收益率和日期顺序。教学 CSV 的本地 SHA-256 为 `8ba35626a8dedd2e89f340c99964a941e0189904387e6e0fa7805510420cfe3c`。作者原始文件的哈希、格式读取依赖及开发期样本另行核查。[复现命令与本轮练习](lesson-02.md)

<a id="mlf-w02-author-sample"></a>
## 作者文件与训练期摘例（2026-11-22，A 组反馈后）

原始文件来自书中第 1 章为教学复现指定的作者仓库，文件名为 `material/data_ml.RData`，固定提交为 `572b22acd4dbf58ef9a6dadbdcd976344d3af1d4`。本地文件与该提交的 GitHub 元数据均为 22,812,797 字节，Git blob 对象号均为 `740bd18b43ccbc42287a4311c079905b2ce89db1`。本地 SHA-256 为 `eb561b24eeae60de9c3f335f0d388dcd1ed9b04243790aef3ce88d616a44b774`。原件放在 `data/ml-factor/raw/<固定提交>/data_ml.RData`，两行练习摘例另存于 `data/ml-factor/w02-development-sample.csv`。两个文件均由现有 Git 规则忽略。进一步使用或再分发的权限尚待核实。[作者数据说明](https://www.mlfactor.com/notdata.html#dataset) · [固定版本文件](https://github.com/shokru/mlfactor.github.io/blob/572b22acd4dbf58ef9a6dadbdcd976344d3af1d4/material/data_ml.RData)

原件是 gzip 压缩的 RData，序列化格式版本 2，由 R 3.5.3 写出。对象 `data_ml` 有 99 列。读取器用本地独立的 Python 3.14.6、pyreadr 0.5.9 和 pandas 3.1.1，完整实测版本见[副线依赖](../../../requirements-ml-factor.txt)。`pip check` 通过。这里直接读取作者的 RData，与书中 Python 示例从预先准备的 CSV 读入的方式不同。

选样先固定训练段内的 2013 年 10 月和 11 月，使两行的次月标签都落在训练年份内。定位时从文件开头的 450 行中仅比较 `stock_id` 和 `date`，取首对同一股票、这两个月相邻的记录。查得文件内编号 228，从零计数的行偏移为 319 和 320。读取脚本复核文件 SHA-256 及这两个键，最后输出四列。pyreadr 解码 RData 时会扫描列的原始字节，行限制作用在返回的记录上。本轮仅查看训练期两行的特征与标签，未单独查询、汇总或绘制验证期和测试期收益。两行用于读表，研究实验仍为 0 次。

| 字段 | 读者可以怎样解释 | 精度及时点 |
| --- | --- | --- |
| `stock_id`、`date` | 文件内股票编号与月度观察日期。样本编号为整数，两个日期值转为 Python 日历日期。 | 2013-11-30 是周六。样本日期可标记所属月份，缺少时分、时区、报价或交付时间。 |
| `Mom_11M_Usd` | 原始概念是以美元价格衡量从往前 12 个月到往前 1 个月的价格动量。作者第 4.4.2 节确认按日期、按特征做经验累积分布变换，无并列时等于升序名次除以有效股票数。分数为无量纲的相对位置。 | 本地样本为浮点数。逐股原始价格、价格调整细节、生产时的并列和取整实现、实际交付时间及修订情况尚待证据。 |
| `R1M_Usd` | 当前观察行对应的随后一个月含分红总收益率，小数乘 100 得到百分数值。作者回测用收益率加 1 复合。 | 月度方向有作者依据。每笔的确切起止报价、具体交付时间、退市等个别情形未从两行查明。 |
| `Vol1Y_Usd`、`Mkt_Cap_12M_Usd` | 已确认字段存在。原始含义分别为一年收益波动率和美元计价的 12 个月平均市值。作者对输入特征作了横截面变换。 | 本轮摘例输出前述四列。这两个备选特征的精确计算和可得时点仍待查。 |

以上原始定义与变换来自作者资料，字段名和样本值另经本地读取。上游明细、精确历史可得性和实际成交价格仍待补证。[字段表](https://www.mlfactor.com/data-description.html) · [Python 数据章](https://www.mlfactor.com/material/CHAPTER_1.html) · [Python 回测章的收益用法](https://www.mlfactor.com/chap_12.html)

**复现**　从仓库根目录运行下列 PowerShell 命令。已准备好环境和原件时，只需最后一行。首次取得原件时，可从上方固定版本文件页面下载到所示本地路径，脚本在解码前核对字节哈希。

```powershell
py -3.14 -m venv mlf_lesson_works/.venv
& '.\mlf_lesson_works\.venv\Scripts\python.exe' -m pip install -r requirements-ml-factor.txt
& '.\mlf_lesson_works\.venv\Scripts\python.exe' -I -X utf8 src/research/ml_factor/read_week02_sample.py
```

<a id="mlf-w02-uniformization"></a>
### 对动量变换的核查订正（2026-11-22）

此前的数据章核查只记录了“做过变换”，把仍待核实的范围写得过宽。作者的预处理章明确给出按特征、按日期分别作均匀化的方法。对一个月内某项特征，用经验累积分布函数计算不高于该值的有效股票数占比。无并列时等于原始特征的升序名次除以非缺失股票数。这说明可以将 0.62 解读为当月该特征由低到高约第 62 百分位。[作者原书第 4.4.2 节](https://www.mlfactor.com/Data.html#scaling) · [官方 Python 第 4 章同节](https://www.mlfactor.com/chap_4.html)

原始字段的美元价格动量窗口见作者字段表。课堂用相同口径的两端价格、无拆股分红的虚构股票演示累计价格变化。原件中的两行已重新读取，包含股票编号、观察日期、动量分数和未来总收益率，摘例未包含原始价格序列。从已发布的分数无法反推出原始动量、未取整名次或精确交付时间。书中的总体变换方法、课堂价格假设和逐行仍未知的实现细节分别记录。[字段表](https://www.mlfactor.com/data-description.html) · [本课完整算例](lesson-02.md#mlf-w02-momentum)
