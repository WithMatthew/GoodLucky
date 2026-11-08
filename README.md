# 量化投资学习与实践

从投资零基础出发，以美国股票和 ETF 为方向，在 Codex 中完成讲解、练习、Python 实验、回测与模拟交易。

当前学习安排为每周 5 天、每天 1 小时，共 24 周、约 120 小时。建议从 2026 年 10 月 5 日开始，基准完成日期为 2027 年 3 月 21 日；补课和休假会使日期顺延。

- [24 周学习与实践计划](docs/learning-plan.md)：每周主题、产出和验收标准。
- [学习进度](docs/learning-progress.md)：当前课次、完成记录和待解决问题。
- [学习与续接流程](docs/learning-workflow.md)：重新打开后的恢复顺序，以及每轮保存规则。
- [第一周任务](docs/lessons/week-01.md)：五天安排及第一课练习。
- [协作指南](AGENTS.md)：研究、代码和交易操作约定。

## 关闭后怎样继续

下次在 Codex 中打开同一个本地文件夹 `D:\ai-learnning\good_lucky`，在原聊天或新聊天里说：

> 继续学习。

Codex 按仓库说明读取进度和课件，先告知恢复位置，再继续教学。默认沿用每天约 60 分钟的安排；有不同时间时可以直接说“继续学习，今天有 30 分钟”。时间预算不等于实际已学时长。

中途结束时说“今天先到这里，保存进度”，等待保存完成的回复后再关闭。每轮练习反馈也会按约定保存，因此可恢复到最近成功写入的检查点。进度保存在本地文件，换电脑时需要携带这些文件；尚未写入的回答不能靠关闭操作自动保存。

如果打开的环境没有自动读取仓库说明，可以明确说：

> 请读取 AGENTS.md、docs/learning-workflow.md 和 docs/learning-progress.md，按续学检查点继续学习。

课程已经开始，最新课次和时长统一查看 [学习进度](docs/learning-progress.md)，此处不重复维护。研究环境尚未安装，行情与账户尚未接入。阶段目标是能解释、复现和质疑一项简单投资研究；不以盈利或开启实盘作为结业条件。

## 数据的 Git 追踪与 GitHub 同步

`.gitignore` 对数据采用逐项放行的方式。目前可随仓库提交虚构教学样本，以及下列 SPY 教学文件：

- `data/raw/ssga/spy_nav_2026-11-08.xlsx`：原始快照。
- `data/derived/spy_nav_2024-01-02_2024-01-08.csv`：课堂使用的五行净值样本。
- `data/derived/spy_nav_2024-01-02_2024-01-08.metadata.json`：来源与文件校验值。

`.gitattributes` 让数据目录中的 CSV 和 XLSX 保留原始字节，避免不同设备的换行符转换改变已记录的 SHA-256 校验值。

在仓库根目录执行以下命令，可将规则、说明和数据一并提交到当前配置的 `origin/master`：

```powershell
git status --short --untracked-files=all
git add .gitignore .gitattributes README.md docs/data-sources/spy-nav-teaching.md data/raw/ssga/spy_nav_2026-11-08.xlsx data/derived/spy_nav_2024-01-02_2024-01-08.csv data/derived/spy_nav_2024-01-02_2024-01-08.metadata.json
git diff --cached --stat
git commit -m "Track SPY teaching data and metadata"
git push origin master
```

修改忽略规则后，文件会先显示为未追踪（`??`）；`git add` 后才进入暂存区，完成 `commit` 和 `push` 后才会出现在 GitHub。推送成功后，其他设备通过克隆仓库或 `git pull` 获取同一份数据。

以后新增需要同步的小型数据文件时，在 `.gitignore` 中添加对应文件的 `!` 规则；新建子目录还需要逐层放行父目录。其他行情、缓存和本地数据继续默认忽略，避免批量带入账户记录、大型数据集或无权分发的数据。数据来源与处理规则见 [SPY 样本说明](docs/data-sources/spy-nav-teaching.md)。
