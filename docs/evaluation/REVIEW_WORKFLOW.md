# 离线人工核源与费用对账流程（current-3，待执行）

本流程适用于 [现行协议](CURRENT_EVAL_PROTOCOL.json)的 P-02 pilot 和 P-04 正式批次。它是验收记录的操作约定；官方真实性、实际权限和费用账单仍须人工核对。每次付费运行单独授权后执行，历史 r12 记录不作新批次输入。

1. 运行前冻结协议、代码、模型、预算、评分、环境和来源窗口，记录独立 task/run ID 与授权引用；确认项目总账中已花金额、剩余额度与本次保守费用上限。无法界定费用或余额不足时停止。
2. 每次尝试结束后保存原始尝试、脱敏逐调用 trace、报告快照（没有报告填 `null`）和离线复核文件。路径相对于批次结果 JSON，逐文件计算小写 SHA-256；失败、取消、中断和重跑均保留。复核文件的 `report_sha256` 与报告快照一致，包含 task/run ID、状态、事实、来源定位、人工复核、已知/未知费用和可比条件。
3. 核源人逐字段、逐实质结论打开官方仓库/文档/发布页，记录主体与版本、官方身份依据、最小片段、页面定位、fact ID、查验时间及核验人。社区经验只标补充来源和局限，不支撑关键结论；条件化建议逐项对照已核实的 fact ID。矛盾或不可核实项标冲突/未核实，不改写原始报告。
4. 所有候选 `completed/full` 和冲突尝试须在稍后再打开官方来源二次核验，记录同人或独立核验、时间及结论。改动报告内容就生成新快照/哈希并重新复核，旧复核文件及哈希保持可追溯。
5. P-02 pilot 的账户访问检查未实施时填 `null`；只报告研究字段与来源诊断，不能写作正式 full 成功。P-04 对每次正式尝试核对 owner/另一成员权限、取消权限及 UI/API/PostgreSQL/SSE，三个访问检查均须实际布尔结果。正式 full 还须满足报告、人工来源与建议的全部条件。
6. 将每次尝试加入项目总账：run/task ID、所属 pilot/diagnostic/formal/contingency 预算、批次 ID 或 `null`、授权引用、原始记录路径/哈希、已知费用、总费用或 `null`、未知调用数。已完成的 pilot/正式批次以结果 JSON 及哈希登记到 `batches`；中断和诊断条目即使没有完整批次也入账。
7. 运行 `python scripts/validate_project.py --results <批次结果.json>` 和 `python scripts/validate_project.py --ledger <项目总账.json>`，保存命令、退出码与输出；另由人工核对 provider 用量/账单是否有漏记。校验器只能验证声明、交叉引用及文件字节，不能自动判断官方身份、真实权限或账单完整性。

账本 JSON 顶层为 `protocol_version`、`batches`、`entries`。每个 `batches` 项包含 `batch_id`、`phase`（`pilot` 或 `formal`）与 `artifact: {relative_path, sha256}`。每个 `entries` 项的必填字段见协议 `project_ledger_contract.entry_required_fields`；`evidence_artifact` 同样使用相对路径与哈希，指向该次原始记录。`batch_id=null` 只用于未纳入完成批次的诊断/中断/重跑；每个 run ID 全项目唯一。机动费用必须有单独授权引用，且不提高其他阶段限额。

总账是**所有新增真实尝试**的唯一项目费用索引；其校验结果与人工账单对账记录一起进入最终 Go/No-Go 证据包。未知费用保持 `null`，不得以已知下界代替总额或写成零。
