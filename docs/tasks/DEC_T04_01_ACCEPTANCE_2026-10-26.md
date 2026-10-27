# DEC-T04-01 硬条件变化离线对照验收

Task ID：`DEC-T04-01`。实施状态 `IMPLEMENTED`；技术验证 `VERIFIED（限定离线）`；独立审查 `DONE`；人工业务验收 `PENDING`。本页是该切片的唯一任务记录；配置实际使用结果回填[原配置任务](CODEX_LIFECYCLE_CONFIG_2026-10-25.md)。

## 原始要求、批准和边界

用户于 2026-10-26（Asia/Shanghai）在范围确认卡选择“确认此范围并开始”。批准内容：补齐 DEC-AC-04/05 的离线对照回归，固定候选和事实后分别改变硬条件，验证推荐变化、全部不满足时拒绝推荐、报告 fact ID 与“待人工核实”标识；新增测试、生成可查看的离线报告、更新既有验收记录，执行独立审查及范围内测试修复。此次先不改推荐算法、API、数据库或 UI；若发现生产行为违反契约，保留失败证据并另议修复范围。

需求来自 [DECISION-001](../features/DECISION-001/spec.md) 的 DEC-AC-04/05 和[任务表](../features/DECISION-001/tasks.md)中 DEC-T04 的明确对照缺口。遵循现行 SPEC／PLANS／契约／冻结协议；不新增业务需求、不运行真实模型／浏览器评测、不安装依赖。没有 commit、push、创建 PR、合并或发布授权。

## AC、模块、依赖与顺序

| 本切片条件 | 对应要求／模块 | 验证与产物 |
| --- | --- | --- |
| C1：同一候选、事实、偏好，仅硬条件变化，机器候选推荐由 AtlasAPI 转为 BirchAPI | DEC-AC-05；DecisionService → ReporterService | 固定合成事实及模型判断，比较两个实际报告；偏好不覆盖硬条件。 |
| C2：同时要求两项硬条件，每个候选均违反一项，不给赢家并说明缺口 | DEC-AC-04/05；相同链路 | 第三个报告无 recommendation，矩阵和无法推荐理由对应。 |
| C3：矩阵、报告证据 fact ID、主体、URL、片段和时间一致；保留机器／人工核实分层 | DEC-AC-02/04/05 的本地展示回归；ReporterService／现有模型 | 三个报告均标待人工核实；不会将样例当官方事实或正式 full。 |

依赖：复用已实现 T02–T04 和既有固定判断方式，无新生产依赖。顺序：基线与保留清单 → 新增单一测试文件 → 聚焦测试和样例报告 → 完整差异自检 → fresh-context 独立审查 → 核实／修复／复测／必要复审 → G6 人工验收包。直接进入 G5，未触发 G1–G3 的新设计。预计半天内的小切片，含测试、Review 与证据整理；主要不确定性是既有行为是否符合对照条件。

本次风险为测试与验收证据范围的 R1；不修改生产决策指导、持久状态、权限或外部调用边界。若需生产行为改动，重新评估风险与授权。本次不把测试覆盖扩大解释为推荐算法已正式验收。

## 基线和保留

基点／当前 HEAD：`e70b5f983532868b765e988f9162ddf989cf153d`，分支 `main`。开始前 9 个既有配置修改及 1 个未跟踪配置记录，暂存为空。字节快照和清单在 `.tmp/lifecycle-usage-20261026/baseline.json`；共享源 23 文件与项目 10 文件已留基线副本，安装的 14 文件与维护源字节一致。共享仓库文件均未跟踪；不将它们认作本轮新建。

| 命令／目录 | 基线结果 |
| --- | --- |
| `..\.venv\Scripts\python.exe -m pytest tests/unit/test_decision.py tests/unit/test_reporter.py -q`；`backend/` | exit 0，13 passed in 0.73s。 |
| `.\.venv\Scripts\python.exe scripts\validate_project.py`；项目根 | exit 0，offline validation passed；真实模型能力和来源真实性未验证。 |
| `.\.venv\Scripts\python.exe .tmp\lifecycle-usage-20261026\capture_baseline.py`；项目根 | exit 0；项目 10、共享 23、暂存 0，部署 14/14 字节相同。 |

范围：新增 `backend/tests/unit/test_decision_condition_changes.py`、本页、任务表进度及原配置验收记录增量；生成可重跑的本地样例及审查证据放入已忽略 `.tmp/lifecycle-usage-20261026/`。原 9 个配置指导文件保持不变，原配置记录只追加本轮证据。共享源仅更新 `docs/ACCEPTANCE.md`，写入须遵循实际文件权限。生产源码、四入口、历史原件、browser-use 和 CI 不改。

## 实际检查、独立审查和人工验收

新增单一测试文件，三个测试通过实际 DecisionService／ReporterService 运行同一固定事实目录和固定结构化模型响应。模型替身不访问 provider，`StructuredCompletion(0, 0)` 是夹具值，不是任何真实调用的费用或 usage 观察。AtlasAPI、BirchAPI 均为虚构候选，来源使用 `.invalid`；不把材料称为官方核源或真实研究。

| 命令／目录 | 实际结果 |
| --- | --- |
| `..\.venv\Scripts\python.exe -m pytest tests/unit/test_decision_condition_changes.py tests/unit/test_decision.py tests/unit/test_reporter.py -q`；`backend/` | 首轮 exit 0，16 passed in 0.65s；格式修复后 exit 0，16 passed in 0.37s。新增 3 项；既有 13 项保留通过。 |
| `..\.venv\Scripts\python.exe -m ruff check tests/unit/test_decision_condition_changes.py`；`backend/` | 首轮 exit 1，I001 导入排序；`check --fix` 修复后再次 check exit 0，All checks passed! |
| `..\.venv\Scripts\python.exe -m ruff format --check tests/unit/test_decision_condition_changes.py`；`backend/` | 首轮 exit 1，1 file would be reformatted；格式修复后再次检查 exit 0，1 file already formatted。 |
| `.\.venv\Scripts\python.exe .tmp\lifecycle-usage-20261026\render_samples.py`；项目根 | 首次沙箱运行无返回，已中断，不能计成功。带 `faulthandler.dump_traceback_later(8, exit=True)` 的诊断 exit 1，栈停在 Windows asyncio `_make_self_pipe → socket._fallback_socketpair → accept`。 |
| `.\.venv\Scripts\python.exe -u -c "import faulthandler, runpy; faulthandler.dump_traceback_later(20, exit=True); runpy.run_path('.tmp/lifecycle-usage-20261026/render_samples.py', run_name='__main__')"`；项目根 | 经执行工具批准在沙箱外重跑，exit 0；生成 3 组 Markdown／JSON 和索引／哈希清单，没有 provider 或外部网络服务调用。 |
| `.\.venv\Scripts\python.exe scripts\validate_project.py`；项目根，更新记录后 | exit 0，offline validation passed；能力与来源真实性仍未验证。 |
| `.\.venv\Scripts\python.exe D:\codex-engineering-config\scripts\validate.py`；项目根 | exit 0，configuration structure: PASS。仅校验结构与链接，不证明行为。 |
| `git diff --check`、`git diff --cached --check`；项目根 | 均 exit 0；既有两项 Skill 有 LF／CRLF 提示，无空白错误，暂存仍为空。 |

没有发现需要改变生产行为的失败。实际 AC：C1、C2、C3 均已离线验证；人工官方核源、真实推荐价值、UI/API/SSE/数据库链路及崩溃恢复未测试。此次未改这些模块，不扩大到完整 E2E、PostgreSQL 或正式评测。技术验证、AI Review、人工业务验收及产品 Go 分别判定；P-02 与 r12 No-Go 不变。

独立审查：已实际调用 `reviewer`，任务名 `/root/lifecycle_usage_review`，`fork_turns=none`，不继承实现者推理及预设发现，给出原始要求／批准／AC、规范、四类差异、全部任务新文件、源文件和实际输出；共享 workspace-write 权限，不宣称只读隔离。审查期间 45 份快照与活内容一致，manifest SHA-256 `bb674e6d7c61853cb31d7c8186fb291696996caf070d73ee6ddf3c98c5f69da9`；committed.patch、staged.patch 为空，完整 unstaged.patch 29,372 字符。原 9 项项目配置、其余 22 项共享源、14 项部署文件及原记录前缀独立核对保留。

结论 `DONE`：没有有证据的 P0–P3 发现；覆盖需求符合性、正确性、合理回归、报告和状态准确性。审查侧实际 Ruff check／format --check（均 --no-cache）、Git 差异空白检查、哈希／基线／报告一致性核对通过。首次辅助检查因默认 GBK 解码失败，显式 UTF-8 后完成。审查侧 pytest 首次无输出挂起，中断 exit 1；8 秒定时诊断也 exit 1，未收到栈或测试结果，原因未知，不能算审查者复跑通过。审查者核对主代理原始工具输出 chunk `542384` 的 16 passed／0.37s 和 chunk `8cbf1f` 的生成器 exit 0／六工件哈希，与实物一致。技术测试证据与独立复跑结论分开。

无须行为修复，未触发修复后的行为复审；不能把“无发现”说成缺陷修复闭环也通过。原审查结果保存在 `.tmp/lifecycle-usage-20261026/review-result.md`。上述身份绑定的是回填审查结论前的固定内容；本次回填只改变证据／状态，不改变测试或报告行为，后续文档一致性另核对，不重用旧 manifest 假称新字节一致。

## 可运行结果与人工步骤

在项目根运行 `.\.venv\Scripts\python.exe scripts\render_decision_condition_samples.py --output .tmp/decision-condition-reports`，从已提交的固定测试夹具生成三组报告。如遇同一 Windows 内部 socketpair 沙箱阻塞，按执行工具权限批准重跑。测试可在 `backend/` 按上表复现。生成器随源树交付，报告写入本机缓存；新检出运行此命令即可生成，不依赖原本机 `.tmp`。

运行后打开 `.tmp/decision-condition-reports/README.md`，依次查看 Markdown 及 JSON：

1. `async`：硬条件为 async request handlers，推荐 AtlasAPI，尽管其 small footprint 偏好不满足；依据为 atlas-async／atlas-size。
2. `embedded`：只将硬条件改为 in-process embedded storage，推荐 BirchAPI，依据为 birch-embedded／birch-size。
3. `both`：要求两项硬条件，两个候选各违反一项；无推荐对象，报告保留 Decision gap 和双方反证。
4. 比较三个 JSON 的候选、偏好、证据原片段及时间，检查矩阵 fact ID 能定位到 evidence_facts；输出均为 machine_admitted_human_unverified，Markdown 保留 human verification 提示。确认它们只是合成离线样例，不是对真实项目的判断。
5. 用户亲验输出并给出关键业务行为／协作体验是否接受的结论；当前均为 `PENDING`。

原本机历史样例的三个 Markdown SHA-256（不用于核对新生成输出）：async `9312062e23bf423c2ac435dda638aa9e8b79292ad442c9ee5372fc23d81ef22d`；embedded `04a8a9a4b95fd94cac2f86734d67817028745b31746aa5e50dc4c882b56c910b`；both `874491d585ac19c635605fb9ed339f2260df9ada2a188e13add37a6b22de31f1`。JSON 完整哈希在同目录 manifest.json；重新生成后需重新核对新工件身份，不能沿用旧哈希。

回滚：仅按本轮新增／增量撤回测试和记录，先比较基线，保留既有工作；不用 reset／clean。生成文件不自动清理。未执行提交／暂存／远端操作。

## 2026-10-27 提交前审查修复

用户本轮明确要求“审查当前git 更改，修复，然后提交”，覆盖当前改动及范围内修复的本地提交。历史各轮未获 Git 授权的记录按当时事实保留。本轮补齐可提交的报告生成器，修复新检出无法运行人工验收的问题；报告与原始审计副本按用户最新要求仅留本机缓存，不提交。固定事实、判断及生产算法不改。原 `.tmp` 工件保留。报告重新生成时含可变生成时间，需核对新 manifest，不沿用旧报告哈希。实际检查和独立复审见[本轮记录](../audits/GIT_REVIEW_2026-10-27.md)。人工业务验收仍 PENDING。
