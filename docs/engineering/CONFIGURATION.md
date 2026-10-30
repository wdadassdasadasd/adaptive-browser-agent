# 工程配置与环境资格 — PREP-BASELINE-20261029

40路径工程基线及限定validator/旧入口guard获批；实际落地、检查、独立审查和唯一18项由[连续记录](../features/DECISION-001/tasks.md)判定。行为参数由[SPEC](../../SPEC.md)、[PLANS](../../PLANS.md)、[当前契约](../contracts/CURRENT_CONTRACTS.md)和[唯一协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)定义。本页说明配置与资格，不新增业务权限。

## 配置归属与流程

共享源D:\codex-engineering-config历史安装/发现见[生命周期记录](../tasks/CODEX_LIFECYCLE_CONFIG_2026-10-25.md)，本批不改共享仓库、用户规则/技能/角色、模型、MCP、系统权限或依赖。共享engineering-workflow选择分支→项目[G0–G7](WORKFLOW.md)承载关口→三项本地Skill提供方法，返回同一任务记录；不建立平行编排。已有Spec Kit项目保留主编排器。

| 入口 | 触发及验证 |
| --- | --- |
| AGENTS | 产品/架构/授权变更后更新简短导航；实际收到规则/链接不等强制门禁 |
| .agents/skills | 评测/真实trace诊断/已授权业务按需读取；普通单测不触发全套评测；方法不授权限 |
| WORKFLOW/TASK_TEMPLATE/STRATEGY | 生命周期/具体任务包/风险检查；只读指令不是只读沙箱 |
| .github | 模板填真实AC/检查/审查/权限，CI声明与远端执行/branch protection分查 |
| validate_project | 新协议/材料/映射/数字/历史显式Git字节/技能与链接；不证明语义效果 |

当前会话收到根规则/项目技能，不证明未来桌面/CLI/IDE全已加载；未实测端标待验。无项目级模型/权限覆盖需求，不新增.codex配置/Hook或虚构自动门禁。缺共享Skill直接执行项目流程，缺独立审查保持pending。

## 日期化环境与账目证据

| 观察 | 限制与下一步 |
| --- | --- |
| 2026-10-27 Windows Python3.12.13；browser-use0.13.10/FastAPI0.142.2/asyncpg0.32.0/Alembic1.20.0/SQLAlchemy2.1.3/MCP2.1.1/cryptography50.0.2/pytest9.1.1/ruff0.16.10 | 当时部分导入通过/head20261023_07，不证明Linux环境/新库可运行，不自动升级 |
| Node PATH23.11.1，已有ignored22.23.4，.nvmrc/CI22 | 检查用已装准确版本，不改锁/自动安装 |
| 2026-10-29普通WSL/CIM读查询拒绝，工具级只读提权观察Ubuntu/Stopped/WSL2 | 未启动，不是没安装证明；旧Ubuntu24.04.1/Pg16.15/5433只旧日期证据 |
| 同次逻辑CPU20/RAM15.63GiB/free2.43GiB，C free105.57GiB/D39.59GiB | 瞬时资源，不证明4GiB组可用；不停止其他程序或改WSL |
| 已读.wslconfig mirrored/dnsTunneling/autoProxy/localhostForwarding开启，未设memory | 非隔离资格；transport禁ambient proxy；任何调整另授 |
| browser-use gitlink7be96ed8bafa8dfe1eef228b59cf5c884b8b2431 | 内部Git工作树未知，不把研究commit当已运行版本 |
| LangGraph研究commit声明1.2.16/checkpoint-postgres3.2.0，现锁无这些/Argon声明 | 非安装/兼容证据，02先解析精确依赖身份，失败不改引擎/升级无关依赖 |
| 官方Tokenizer recipe0.2.0模板差异，部分位置未见age/gpg/7z | 非全盘不存在证明；没安装/执行，正式完整请求资格待验 |
| 2026-10-26 21:39:41北京时间CNY10.57 grant0/topup10.57 | 旧授权只读快照，非当前余额/grant/完整账；未重复查询 |
| 声明ledger与r11账核查只覆盖声明范围 | 合并去重/冲突/供应商差额及unknown待闭合，不能填0 |
| 2026-10-27 SQLite只读immutable、task0、无call/cost/budget表；SHA1cf908a6f9e83985548ba7bd0753a204e6d8ccbaf70ac34daa9d3152ecbd0064 | 原件不补全费用历史，不自动导入新库 |
| P-01假48/48，r11/r12真实失败及旧四项中断检查 | 当时内容证据，不给新路径通过；中断不写pass |

## 后续环境与权限包

| 关口/负责人 | 准确产物、时点和停线 |
| --- | --- |
| ENV-M1-01 / AI准备、本人批准 | boot前核旧systemd/bootcommand/launcher自动服务及出站；无证据不先启动。必要时先提出离线取证/宿主隔离的具体权限、路径、影响方案，再核Linux source/venv/binary/data绝对路径、代码锁/UID/日志/角色 |
| 新库 / 首工前 | 资格通过已装PG16目标16.15，独立data/config/凭据/55432/ara_m1与ara_m1_test；旧5433不自动停删。app/checkpoint运行角色无DDL，migration/restore角色另设；建库/迁移/清理各自准确授权 |
| 冷切 / 新入口前 | 旧准入关→队列/在途/unknown→旧API/Worker停止→旧写凭据失效及存活连接→验证不能误写；仅改.env或新握手不足，原件/费用/撤销及只读取证保留 |
| 资源 / 能力资格前 | 父4GiB/CPU4含所有子组和backup，实际峰值/连接/CPU/磁盘测量；WAL/index/checkpoint/backup另计，max_wal_size非硬磁盘界，失败不脱组 |
| 资金 / 首pilot前 | account非秘密ID/时段/run/call/hash、重复冲突/known/unknown/inflight/供应商差额；实际币种/≤24h价格/credit/grant/整批最坏预留，无法闭合paid off |
| Tokenizer/Gateway / 正式研究前 | 完整请求/模板/公开model/字段，thinkingdisabled/maxoutput/同bytes/repair0；首次有限诊断另授不循环前置 |
| ENV-M1-02(08a) / 首pilot前 | 独立介质借优先、采购另授；纸钥本人离线/纸卡cipher与manifest原字节hash、age来源身份、从纸录钥真实恢复，实际介质/钥/资格缺 |
| Browser / 开启前 | DNS/v4/v6/redirect/subresource/UDP/旧连接、临时TLS信任、CDPpipe/bridge和gen监督源码/对抗实验，失败0不回个人profile |

环境启动可能写状态，不作只读探针。准确路径/权限未核时不能占位符执行；代码、依赖、WSL启动、cluster/role/migration分别有适用批准。首工只有auth/draft最小sup，不承接完整paid恢复。实际资格缺阻对应运行，不伪填已验证。

## 连续资格、备份及回滚

sup启动无资格，DB OPEN/同UUID非最新。监测PG持续连接与postmaster start，池新连接/重连同步核对；失连续封gen、隔离旧身份/研究/Memory。只有同Sup/PG持续时API/Worker新actor可加入。另授CLI新凭据只开草稿/history，恢复资料新ID不复活Memory，无独立最新性证明不恢复paid。不自动检测任意superuser在线restore，运维先seal/停写另授。

BK-r3.2按契约：同export snapshot dump/manifest、Linux字节pipe/流式限额；捕获校验不等restore。独立纸卡两hash先验→完整解密→精确隔离restore，失败目标不接应用/旧库零写，不称目标零SQL。纸钥长期离线与可信本机短时解密分开；tmpfs不证明无swap/pagefile残留、不承诺物理擦除或擅改宿主页。首pilot前独立物理介质与纸钥真实恢复仍是硬前置，合同参数不等实际已验。

回滚先停写，保新数据/费用/授权，只回理解当前schema版本，不destructive downgrade/不让旧binary写新库。配置回滚只恢复本批task-owned进入字节，保其他工作；ignored审计材料绑定快照/完整patch/检查，不新增旧方案归档。

## 费用、投入与交付

新增epoch为2026-10-28本次重评开始；本人称仓库外无新增，不推断仓库/历史未知0。条件最坏296.46及116model/84Search/168Fetch/56GH见唯一协议；<300非到账/grant/调用权限，所有新增纸耗/介质/DR/收费审计不得桶外藏。

2026-10-29起七至八周、本人≤20h/周，估算100–144h/AI260–420agent-hours见PLANS，首周实测校准；12月17–24日不是已证明足够。超窗提具体取舍，不暗删核心。

本批40路径配置/guard→完整检查/正文/patch/指纹→非作者实际文件审查→修复重测复审→18项判定，随后停首业务授权前。远端CI/分支门禁没查不称启用；业务、安装、环境/DB、真实调用、购买、Git写另授。技术、审查、本人业务/价值/掌握、Go和发布分开。
