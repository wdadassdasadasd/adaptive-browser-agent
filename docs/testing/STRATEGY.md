# 按风险选择的测试与Agent评测策略

当前设计为PREP-BASELINE-20261029；[SPEC](../../SPEC.md)、[功能AC](../features/DECISION-001/spec.md)、[现行契约](../contracts/CURRENT_CONTRACTS.md)和[唯一协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)定义行为及门槛。本页选择验证方式，不新增分母或Go规则。实际命令、结果、独立审查和18项结论只记[连续任务](../features/DECISION-001/tasks.md)。

| 层 | 对象及触发 | 证据边界 |
| --- | --- | --- |
| L0 | 引用/JSON/schema/锁/数字/格式/类型/范围与指纹 | 结构通过不证明真实来源或语义 |
| L1 | 状态、解析、选择、准入、预算及失败逻辑 | 离线fixture不算真实任务成功 |
| L2 | API/DTO/事件/归属/数据库约束及兼容 | 严格错误码和无孤立对象 |
| L3 | 真实受限隔离Pg、独立连接并发 | Mock/同连接/缺库skip不能替代 |
| L4 | Vue→API→持久确认/历史/取消/授权 | Windows UI关键操作须本人亲验 |
| L5 | 崩溃、失租、DB断线、unknown、资源和恢复 | 保留两种竞争顺序及实际进程证据 |
| L6 | 另授权真实Agent任务、原文核源/计时/费用/优化 | 与离线、人工修稿和Go分开 |

## 获批配置批次检查

40路径只实现配置校验及旧入口误用guard。检查JSON解析/关键类型/唯一协议/M1引用hash/六题输入与scorer隔离、稳定ID/映射、当前链接、数字预算、固定Git历史字节及显式换行变换、范围外原字节、完整diff/新文件/指纹。旧runner/budget arm/reconciliation的直接调用及CLI面对新/坏/缺失协议，必须在Settings/engine/client/目录/账本写入前拒绝。历史只读不扩账、不arm、不授予新执行。

从backend工作目录重点运行：

```text
pytest -q tests/unit/test_validate_project.py tests/unit/test_current_evaluation.py tests/unit/test_pilot_runner.py tests/unit/test_pilot_capture.py tests/unit/test_project_ledger.py tests/unit/test_pilot_cost_reconciliation.py tests/unit/test_legacy_entry_guards.py
```

只使用已安装依赖，运行适用Ruff/format-check及离线回归，不自动sync/install。测试临时输出和审查快照放限定ignored目录；DB/服务/真实调用不由配置检查授权。CI的Python/Pg checkout包含固定Git历史所需深度；声明不等于远端已执行。

六题实际正文/澄清卡/等价性/决定性主张/critical failures由制题者与非作者审查者核对，不在进度中提前展示。公开仓库不构成盲测；材料未审不能称协议全冻结。

### CONFIG-RAWJSON-20261030 限定修复

本专项另获五文件批准，承接原40路径，不改变协议正文、原字节hash、业务权限或历史解析。CURRENT协议、DISCOVERY材料、M1引用三份原始输入都须严格JSON解码：任意层重复键（含转义后相同键）、NaN/正负Infinity及指数溢出非有限数值均拒绝；有限int/float保持原类型。只报固定错误类别及文件角色，不输出键、值、题面或JSON异常原文。材料output_requirements为非空字符串列表且每项非空白；variant与有效case ID后缀一致。字符串语义和评分答案隔离仍需独立实际材料审查。

三份原字节绑定JSON使用精确`-text whitespace=cr-at-eol`属性。测试通过只读`git cat-file --filters`，将同一固定Git LF blob按三个目标路径及autocrlf=true/input/false过滤，比较原字节；不写项目Git、不执行checkout，不把过滤器验证称完整clone/CI资格。主动编辑改字节仍由现有raw hash拒绝，不能自动规范化或重绑定掩盖漂移。

专项回归并入上列七文件命令，覆盖三个原始读取入口、错误输出无canary、有效有限数值、六题映射和非法输出要求元素；保留原字节微改拒绝、历史显式换行读取及旧入口guard回归。审查须读取五文件完整正文、本次进入字节增量、累计HEAD完整差异与两份既有新增文件；旧审查只复用于未变化内容。检查失败/修复重测/复审及最终封存仅追加到原审计目录，唯一任务记录和原18项承接结论。该校验器不执行研究或授予调用权限。

## 后续实现验证矩阵

| AC/任务 | 正常和必需失败场景 | 层/验收 |
| --- | --- | --- |
| DEC-AC-15 / DEC-M1-01 | 两真实账号/cookie jar；原文保存/重开/另一owner404；CSRF/Host/Origin；密码/原稿错误不回显；NUL/surrogate/UTF8边界；第4活跃会话429；19稿并发create；reset-login/disable-write双序 | L1–4、真实restrictedPg/屏障，本人亲验 |
| DEC-AC-08/09/14 / DEC-M1-02 | 提议不等于接受；幂等先CAS；异body409、双接受/满队列/DB故障无孤立对象；cancel/success/失租/唯一终态双序 | L1–5，报告/active/event同tx |
| DEC-AC-10/11/12/18 / DEC-M1-03a | 同名/fork不合并；hash去重保出处；空batch/失败非饱和；17未深查阻充分无赢家；未知版本反证不消失；子串不等语义支持；关系超限frontier | 固定资料L1/2，真实核源L6另授 |
| DEC-AC-13/14 / DEC-M1-03b | prepared/admitted/send_claimed；grant/revoke/send/unknown双序；completed本地重处理不重发；请求变更旧许可失效；usage/cache/计价分账；完整请求Tokenizer资格；repair/summary0 | L1–3/5，Tokenizer/model实际资格另授 |
| DEC-AC-17/18 / DEC-M1-04 | 长期意图/原文归属/否定/引用/敏感/假设；负向明确偏好；TTL不续/当前条件优先；rev/expiry/revoke逐项复核；sourcehint别名/新ID不复活；满容量更正先停旧项 | L1–5，真实seed无则pending不加setup |
| DEC-AC-10/13/14/15 / DEC-M1-05 | DNS/v4/v6/redirect/subresource/UDP/QUIC/WebRTC/旧连接；pipebridge/背压/旧gen重连；seal→kill→空组→匹配slot释放 | 连接层实证/对抗测试，未资格Browser=0 |
| DEC-AC-14/15 / ENV-M1-02(08a) | 独立纸卡先验；有效公钥伪造归档拒；坏钥/末块/尾随/超长/磁盘满/单侧失败；同snapshot root；错DSN拒；失败目标隔离；旧密码/cookie/grant不复活 | 首pilot前独立介质/从纸录钥恢复，旧库零写不称目标零SQL |
| DEC-AC-20 / DEC-M1-06 | 原症状/预定义目标/本人最小代码修改；固定源正负回归；独立审查后另授同条件复测；漂移/混杂保留 | 至少真实纠正1项，失败实验不替门槛 |
| DEC-AC-16/19 / DEC-M1-07 | 首揭题计时/全部主动操作；六次同版；原始/最终稿分列；审计仅缺陷；失败取消缺失不替换；全六最终合格才省时中位数 | 唯一协议L6/本人核源，无额外modeljudge |
| DEC-AC-15/19/20 / DEC-M1-08b | 最新备份恢复、证据链/owner/费用/权限保守；成功失败演示及本人解释 | 实现、技术、本人验收、价值、Go分别记录 |

## Tracing、审查与完成

报告→Claim→source表示/locator/hash→Call→上下文选排→安全业务正文→response/usage/费用→代码/协议身份可追。缺工件、坏hash、跨owner应拒；离线重建无网络、不框架replay外调。UI事件满后canonical调用/费用仍完整；secret canary覆盖日志/错误/导出，不采隐藏思维链。未采集/未识别/未绑定/未选/裁剪/摘要失真/输出未体现分别诊断，不推断模型内部使用。

普通行为需fresh-context独立审查；重要设计和安全有相应技术/安全审查。提供原始要求/AC、基点/完整committed/staged/unstaged/new-file、检查和指纹，固定内容；核实发现→修复→重测→受影响复审。自检、旧审查和代理完成消息不替实际文件审查。

本人关键业务验收、代码入口/预测/亲改/回归、技术、AI审查、价值和Go分别记录。未执行/缺权限/缺库/中断诚实标记。旧9/8/12、15次及旧preparation按固定Git1ffade6de07ebe3d1e72afb4c44b8677466eca67原路径/字节身份读取，不再现行准入；[V1矩阵](V1_TEST_MATRIX.md)和带日期原证据保留。
