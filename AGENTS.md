# 仓序项目协作约定

涉及 GitHub 或 Cloudflare 操作时，优先使用宿主机的 `gh` 与 `wrangler`，不依赖受限环境里的凭据。
可以按任务需要调度本地 Kimi Code CLI 和 Claude Code，明确分工；主代理负责审阅改动和验证结果。

## 需求与实现依据

- 开始业务改造前阅读[业务需求与验收](docs/cangxu/REQUIREMENTS.zh-CN.md)，按需求编号关联实现与验证结果。
- 需求编号、验收条件和未决决策以需求基线为准；新增或变更需求时，同步更新需求文件及对应验证状态，不把演示数据或 API 测试描述成业务验收。
- 用户提供的正式流程、验收表单和流程图均作为业务验收输入；逐步骤、分支、签字及归档证据建立需求编号，未被系统完整支持的部分明确列为业务缺口，不因当前代码没有模型或页面而缩减要求。入库归档操作按需求基线 IN-01～IN-06 验收。
- [改造规划](docs/cangxu/ROADMAP.zh-CN.md)和[行业数据模型设计](docs/cangxu/DOMAIN-MODEL.zh-CN.md)是候选技术方案；范围和交付优先级以业务需求基线为准。
- 优先完成入库、领退料、实际装配、质量返工、供应商维修、分批交付和盘点闭环，再深化完整拓扑。按 2026-10-13 用户确认，常驻工作伙伴可并行推进，具体执行动作仍依赖业务规则与验收。
- 工作伙伴实施前阅读[产品规划](docs/cangxu/ASSISTANT-PRODUCT.zh-CN.md)和[技术规划与实施交接](docs/cangxu/ASSISTANT-TECHNICAL.zh-CN.md)：按用户最新截图实现独立工作台：左侧伙伴列表/搜索/新建，右侧连续对话与固定输入条，深色双栏；移动端在列表和对话之间切换。此确认取代此前单栏、禁止侧栏的布局约定；不增加任务看板或执行日志面板。保留右下角入口，Pi Durable 常驻、事件/定时主动工作与恢复属于第一版核心能力。
- 按“模型与迁移 → API/事务 → 虚构数据及端到端验证 → UI 翻译与交互验收”的顺序推进；每阶段记录已实现、已测试和仍待业务确认的边界。
- 复用 InvenTree 的物料、库存、BOM、工单和订单，不另建库存余额体系。区分现有能力、配置项、计划功能与已验收功能。
- 试点期库存唯一业务账已由用户确认采用 InvenTree/仓序；ERP 不得并行回写库存余额。其他主数据权威与同步方向仍以需求文件中的待确认项为准。
- 交换部件与线缆按设备类别、协议、芯片厂商、板卡品牌/制造商及供应商建模，覆盖博通、联瑞等实际产品，不将所有 switch 视为 NVSwitch。规格及兼容关系以工程资料和批准记录为准。
- 不把原始企业台账、客户/人员信息、真实 SN、凭据或生产附件提交到仓库；示例和测试使用虚构数据。
- 实施前处理需求文件中的相关待确认事项，不猜测编码冲突、库存权威或套件数量。来料异常按用户确认采用单步批准/驳回；技术/采购意见可记录但不阻塞处置，不增加逐级会签。
- 入库归档闭环必须覆盖采购单关联、验收记录、可选隔离（默认正常可用）、照片与验收单归档检索、异常反馈、正常/让步/退回分支及单步处置；具体条件以 IN-01～IN-06 为准，功能未实现前持续标记为未完成。
- 按改动范围完成必要检查，并说明本地检查、CI 和现场业务验收各自状态；文档整理不表示功能实现完成。

## 上游贡献与安全约定

See [CONTRIBUTING.md](CONTRIBUTING.md) for codebase guidance.
Security reports must follow the security policy in [SECURITY.md](docs/docs/SECURITY.md) and provide how they interact with the [threat model](docs/docs/concepts/threat_model.md).

Do not open a pull request until a human has manually reviewed the concrete diff. Do not file AI generated issues under any circumstances.
Using AI generated content in issue/PR discussions might lead to code of conduct violations and/or bans.
