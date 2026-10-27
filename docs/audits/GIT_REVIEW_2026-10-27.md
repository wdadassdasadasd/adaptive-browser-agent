# 当前 Git 改动审查与修复（2026-10-27）

用户要求“审查当前git 更改，修复，然后提交”，随后要求缓存与项目无关文件不提交。范围为当前项目改动及审查修复的本地提交，不包含 push、PR、合并或发布。基点／进入时 HEAD：`e70b5f983532868b765e988f9162ddf989cf153d`，`main`，初始暂存为空。初审覆盖57文件全部已提交／暂存／未暂存差异和新增全文；初始内容清单 SHA-256 为 `b7f4b12b828bd17caa04ea009b9d571e6a247312b54cb9f55466c5925bd34835`。

## 发现与修复

Fresh-context `reviewer` `/root/standards_review` 和 `security_reviewer` `/root/spec_security_review`（均 `fork_turns=none`）分别审查规范和需求／文档安全一致性。提供原始要求、AC、项目规范、基点、完整差异、新文件正文、固定指纹和实际检查；共享 workspace-write，初审未写文件，不宣称只读沙箱隔离。初审结束57文件无漂移。

| 优先级／轴 | 核实的触发与影响 | 修复 |
| --- | --- | --- |
| P2／Standards、Spec | M1协议原第47行绑定准备包 CRLF 原字节，但 Git 会规范化 LF；不同平台检出造成冻结校验失败。来源摘录在 Windows 检出也可转 CRLF。 | `.gitattributes -text` 保留新冻结工件原字节；仅对上游来源末尾空行豁免 blank-at-eof，保留片段及清单哈希。正式协议原件不改，M1绑定明确先 CRLF→LF，使用 Git blob 的稳定 SHA，原工作树 SHA 保留为历史观察。 |
| P2／Standards | T04验收原第60–62行只有 ignored `.tmp` 内的生成器和报告索引，新检出无法执行。部分历史审查链接也指本机缓存。 | 提交 [离线生成器](../../scripts/render_decision_condition_samples.py)，复用固定测试夹具；[验收步骤](../tasks/DEC_T04_01_ACCEPTANCE_2026-10-26.md)改为先生成再打开输出。历史本机审查路径明确标注，精简记录保留于本页，原始缓存及生成报告不提交。 |

固定评测输入 `data/evaluation/decision-m1-1/` 是已批准的题面、来源及评分材料，属于项目交付；它们与可重生成报告／工具缓存分别处理。没有修改生产算法、API、数据库、正式题面或 browser-use。新增生成器调用相同固定测试夹具和现有 DecisionService／ReporterService，无网络或供应商调用；生成时间变化须核对新 manifest，不沿用历史输出哈希。

## 实际检查

| 工作目录／命令 | 实际结果 |
| --- | --- |
| 根目录：`.\.venv\Scripts\python.exe scripts\validate_project.py --ledger data/evaluation/ledger-after-e4e3e822-f5f0-582d-9412-e7cb91daefe4.json` | exit 0，offline validation passed。 |
| `backend/`：`..\.venv\Scripts\python.exe -m pytest tests/unit/test_decision_condition_changes.py tests/unit/test_decision.py tests/unit/test_reporter.py -q` | 初次16 passed in 0.54s；修复后16 passed in 0.27s，均exit 0。 |
| 根目录：`.\.venv\Scripts\python.exe -m ruff check --config backend/pyproject.toml scripts/render_decision_condition_samples.py backend/tests/unit/test_decision_condition_changes.py`；相同范围 `ruff format --check` | exit 0，All checks passed／2 files already formatted。 |
| `git diff --cached --check`；暂存blob与受保护工件字节比较 | 通过；正式协议与gitlink未进入改动。 |
| 从暂存分别按 `core.autocrlf=false/true` 用 `git checkout-index --all --prefix=...` 导出，核对材料原字节、哈希、9/8/12槽位、授权关闭及本地链接 | 两种导出各73项通过。该轮包含随后按用户要求移出暂存的报告／审计副本，最终精简范围另外复核，不把旧82文件快照当最终版本。 |
| LF导出目录运行已提交的报告生成器，20秒有界，执行工具批准沙箱外运行 | exit 0，三组报告生成成功，不依赖原本机 `.tmp`。三份 Markdown 与旧样例内容一致。 |

过程失败均保留：生成器首次沙箱内无输出阻塞，主动中断exit 1，后获执行工具批准有界沙箱外重跑成功；初版生成器ISC004／格式失败已修复；首次材料探针将正式协议原字节与Git LF直接比较失败，确认是换行问题后明确哈希范围；一轮validator在新证据文件尚未写入时出现链接缺失，补齐后通过；首次暂存空白检查发现冻结上游来源末尾空行，保留原字节并作限定属性豁免后通过。失败不计通过。

没有运行数据库／迁移、WSL服务、浏览器、真实模型／付费评测、安装或远端CI；这些未由本轮变更触发或获授权。未重新逐页核验全部远端研究来源。人工业务验收／个人理解／正式Go分别待证，r12／P-02／产品仍No-Go。

## 交付与回滚

根目录运行 `.\.venv\Scripts\python.exe scripts\render_decision_condition_samples.py`，输出默认 `.tmp/decision-condition-reports/`；人工按T04步骤核对两个条件切换推荐和双条件无推荐、fact ID及待人工核实标识。候选为虚构，不是对真实项目的判断。

`.tmp`、生成报告、原始审计快照及工具缓存均留本机，不进入暂存。最终清单、完整patch和逐文件worktree/index指纹也只在本机审查缓存，最终Git差异可在提交中核对。本页保存项目必要结论，不复制冗长缓存。回滚仅逆转本次提交内相应增量，保留数据库、历史失败及本机证据；不reset／clean，不自动启旧Worker或付费。新业务任务和远端交付仍需相应授权。
