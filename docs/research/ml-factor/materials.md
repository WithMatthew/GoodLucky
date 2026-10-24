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
