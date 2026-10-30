# 唯一现行评测与历史核验

现行协议为[discovery-m1-1](CURRENT_EVAL_PROTOCOL.json)，由[SPEC](../../SPEC.md)及[现行契约](../contracts/CURRENT_CONTRACTS.md)约束。[M1能力材料](DECISION_M1_PROTOCOL.json)单向绑定它的原字节SHA，不另设资金、分母或Go规则。[六题材料](DISCOVERY_M1_CASES.json)含输入、澄清控制卡与scorer-only参照；输入只准当前题和当前回答，不能注入其他题、评分答案或准备者来源清单。公共仓库不具技术盲性；正文/工具上下文为制备与独立审查所需，面向本人日常报告只显示ID/hash/审查状态，不提前主动展示正式题面或答案。

本批只制备配置、校验及历史误用guard，不实现新runner/ledger/自动计时，也不授权任何真实尝试。材料实际文件审查结果和状态以[唯一连续记录](../features/DECISION-001/tasks.md)为准。JSON结构/hash检查不能证明题目等价、语义支持、账号可用或运行质量。

## 对照与质量

三领域为后台任务/调度、数据存取/迁移、文档解析/生成，每领域两道不同但尽量等价任务。先独立审真实题面、澄清卡、等价维度、全部决定性条件/关键主张及局限。正式逐题首次展示即开始主动计时；每侧120分钟主动/24小时墙钟，批次14天，单次≤7天延期只适用于截止前申请且尚未揭题的确认故障/免费额度刷新。揭题失败、取消、中断、缺失不替换、不改分母。

Agent侧本产品＋本人手工搜索/核源/重写，无外部AI代修或有意复制Control输出/笔记。Control侧固定普通AI方式＋每题一次独立Deep Research＋本人核查。两侧使用同一预注册日常手工引擎清单，可切换、不人为限查询条数，所有操作计时；产品内Search/Fetch配额独立有效。Gemini免费DR仅优先资格候选，账号/地域/入口/次数/普通UI模式未验；不足停，不自动购费或换产品。人脑知识迁移/熟悉度、来源/候选重用和Memory变化逐项披露，不称真正盲评或同模型算法实验。

六个最终本人稿全部达到共同质量后才算三对省时率中位数≥20%。质量覆盖全部接受条件与未知、主体版本/时间、全部硬条件和推荐/排除关键主张官方核源、反证限定/冲突、调查边界和可执行下一步验证，不是固定八事实。有限范围推荐必须真正完成题目要求；quota耗尽/工具失败不能改名充分无赢家。原始Agent/DR结果、技术失败、人工每次改稿与最终质量分别保留，人工修补不把程序失败洗成成功。

主动区间、每次改稿hash/时间、审计绑定、所有缺失/费用字段按唯一协议attempt_record_contract保存。独立审计最多两轮缺陷反馈和一次最终评分，只报缺陷及原稿定位；真正贡献研究资料须披露并计实际时间/新增费用。本人的查源、读缺陷、修改全部主动，纯等待和审计人劳动另列但仍在墙钟。

六次固定代码/模板/工具/Memory政策/评分/额度；protocol和材料hash冻结后只生成一次128bit seed，按协议ARA-EVAL-1确定方法与顺序。准备阶段seed=null/calls=0。正式中修复保留失败槽，新版本完整批次另授权。

## 限额与优化

七个Agent Case为原需求1、改条件能力1、最多优化复测2、正式3；每Case16模型物理槽，另资格2/无关健康2，共116。Search84/Fetch168/GitHub56；条件最坏296.46元包含30元非调用开销及10元未分配buffer。它不是余额、grant或运行授权，价格/币种/历史unknown/在途/完整批次覆盖未闭合时paid关闭。所有linked Turn共享原额度/截止，不能新ID重置。

真实症状→原始轨迹→预定义假设→最小修改→固定源离线回归→独立审查→另授权同条件真实复测。前后来源/模型/环境漂移记录；改输入不当修复，至少纠正一个真实症状仍是M1门槛，两次复测不保证达成。Tracing为Pg业务记录关联视图，offline reconstruct只读旧工件，不重发completed/unknown或执行框架replay。[核源与复核操作](REVIEW_WORKFLOW.md)规定实际证据步骤。

## 历史原件与安全拒绝

旧current-3只解释原B/G/O、15次及旧9/8/12准备，现行路径已原位替换；不新增旧协议归档。历史精确入口：
- Git commit `1ffade6de07ebe3d1e72afb4c44b8677466eca67`，path `docs/evaluation/CURRENT_EVAL_PROTOCOL.json`，原Git LF SHA256 `bc75a1a6d14f7633462538c7c83b79ed5f5bcf0d670997b2000c92caa0002948`。
- 已知旧账本绑定的CRLF表示SHA256 `1c18d53624c21b1e25f5cea5640b4c8b4a5e0cfc001f430c8d603a01d51a8507`，仅显式LF→CRLF可核，不推定其他账本相同。
- 删除的未执行preparation按同commit的 `data/evaluation/decision-m1-1/preparation.json`、原字节SHA256 `481da876ce5794020be05403eb7a75a75f0ce79194a1e40d2f468ca4535bde60`读取；23来源、6份许可及真实授权费用保留。

只读历史核验例（仓库根目录、已有环境，不安装/开库/发请求）：
```powershell
.\.venv\Scripts\python.exe -B scripts/validate_project.py --historical-only --historical-commit 1ffade6de07ebe3d1e72afb4c44b8677466eca67 --historical-path docs/evaluation/CURRENT_EVAL_PROTOCOL.json --historical-raw-sha256 bc75a1a6d14f7633462538c7c83b79ed5f5bcf0d670997b2000c92caa0002948 --historical-newlines lf-to-crlf --ledger data/evaluation/ledger-after-e4e3e822-f5f0-582d-9412-e7cb91daefe4.json
```

旧current/pilot_runner/budget arm/reconciliation遇新/缺/坏协议必须安全拒绝；历史读取不等旧执行、扩账、新reserve或grant。旧已实现runner/账本保留历史回归，新产品运行路径另任务实施。r12/P-02 No-Go不由配置/CI/新M1声明消除，Go/发布分别判断和授权。
