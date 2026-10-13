# 仓序工作伙伴运行服务

Node 24 + Pi Durable / pi-ai / Chord `1.2.0`，使用真正的 SQLite Harness、持久工具任务与独立 HTTP 服务。Django 身份网关、业务工具和本地联调已实现；对话 UI、正式知识资料治理与生产验收尚未完成。详细证据见仓库的 `docs/cangxu/ASSISTANT-IMPLEMENTATION.zh-CN.md`。

```sh
cd src/assistant
npm ci
npm run check
npm run lint
npm test
npm run server
```

`server` 读取被 Git 忽略的 `.env.local`。参考 `.env.example` 配置：

- Django 和 Node 共用 `ASSISTANT_DEPLOYMENT_ID`（小写 UUID）、`ASSISTANT_RUNTIME_TOKEN`（32字符以上）；凭据只放服务端，配置文件权限 `0600`。
- Django 另设 `ASSISTANT_RUNTIME_URL`；Node 设 `ASSISTANT_DJANGO_URL`，默认仅监听 `127.0.0.1:8789`。
- 模型供应商配置为 `fixture` 或 `openai-compatible`；后者需要 base URL（含 `/v1`）、model ID、API key。凭据不写入 Pi agent 文档或前端。
- `ASSISTANT_STORAGE_DIR` 默认 `.state`，每个部署/伙伴由服务端 UUID 映射独立数据库；`ASSISTANT_MAX_PARTNERS` 默认32，范围1～128。
- 金额预算按用户确认不限额；仍有超时、重试与运行限制。每条用户输入默认最多64次新工具意图，`ASSISTANT_MAX_TOOL_CALLS_PER_INPUT` 可设1～128。模型输出默认256 tokens，建议业务配置2048，最高8192；未知费率不以零元元数据描述为免费。

Django 需执行全部迁移并运行 Django-Q2 worker。`post_migrate` 安装唯一持久周期调度，任务关闭浏览器后仍可继续。这里的 Django/Node 服务认证用于关联原登录用户，不是额外的用户授权流程。

## 模型业务工具

配置业务网关后，Pi 实际注册四个工具：

- `business_query`：物料/SN、库存、库位、采购及收货/验收、工单/BOM、实装配置、质量返工、维修、销售/交付、盘点及附件，共24类资源。
- `business_capabilities`：从当前 API 序列化器获取允许字段、必填项、枚举和当前角色是否允许写入。
- `business_action`：13种有限动作：采购收货、耗材领退料、安装/拆卸/替换、登记质量问题/返工、维修收送、登记签收、准备盘点、关联入库附件、将本人对话文件归档至具体业务对象。
- `workflow_knowledge`：带来源、版本及资料缺口的全流程目录；当前是实施指引，不冒充正式 SOP。

桥接固定到 Django `/api/cangxu/assistant/internal/business-tools/`，按服务端伙伴绑定解析当前用户，直接调用原业务 API 的权限、序列化器和事务。模型参数不含用户、grant、任意 URL、HTTP 方法、SQL或shell。签字、本人检验/实盘、审批、测试结论与最终放行保持原业务流程；模型不提供这些自动动作。当前是 Pi typed tools，未实现 MCP server。

工具调用串行。每个外部动作前持久保存命令意图；同一用户输入内，相同规范化动作复用首个命令键，即使模型换 tool call ID 或请求响应丢失，也不会换键盲重试。新用户交办可再次执行相同动作。Django 在原业务变更的事务内保存命令回执；同键异参拒绝。未知结果显示“核实中”。这属于幂等和恢复机制，不是额外授权。

读取工具允许重放；广泛业务动作仍标记 `replay: unsafe`，避免把尚未验证的插件/外部副作用描述成安全重放。模型后续重复同一动作仍使用原命令键核实。每次返回回执也重新检查原业务权限。工具返回最多32KiB，超出时缩小查询页或对象范围；请求超时15秒。

## 常驻与内部协议

所有请求需 `Authorization: Bearer ...` 和匹配的 `X-Assistant-Deployment`；请求体最多64KiB。伙伴存储路径只由服务端生成，启动时恢复已知数据库；容量不足返回503，不驱逐在途任务。

`/v1/partners/{uuid}` 下提供 `GET /status`、`POST/GET /messages`、`POST /controls`、`POST /events`。历史分页最多100条，只展示已持久化的用户/助手文字和站内消息，隐藏思考与工具原文。`POST /messages` 返回持久接收回执，不等于业务完成。同键异文返回409，非空通用引用尚未接通。

确定性入库跟进任务是另外一条后台路径：事件/定时输入固定职责来源与收货对象，执行附件关联、检查和持久站内通知。它的内部范围记录不是模型工具前置授权。普通收货、验收、处置及原生附件变化会写 outbox；周期补查覆盖批量更新、遗漏及乱序。等待缺资料时不持续调用模型。

入库 `ready` 只表示“材料齐备”，不宣称正式归档完成。相同状态不刷屏；网络/限流失败使用原键有限退避，拒绝/耗尽后保留失败记录与必要通知。附件关联不复制或移动原文件，保留来源与摘要；文件变更会使旧证据失效。当前关联文件上限20MiB，更大文件使用原人工归档路径。

停止回复、停止某个任务、停止全部自主写入与停止全部后台工作分开。Django 先保存停止资格再投递取消；全部写入停止不关闭只读检查，已提交业务回执保留。尚未提供完整自然语言停止/恢复解释器与管理 UI。

每个存储用独立 owner SQLite 的 EXCLUSIVE transaction 保证单进程占用，进程死亡后操作系统释放。禁止运行中删除/替换存储或锁文件、使用硬链接或网络文件系统。WAL/NORMAL 的进程恢复测试不等于掉电零丢失、备份恢复或高可用。

已有空闲对话启动时更新为主机模型配置；有未完成 Pi generation/tool/compaction 时保留旧模型。更换模型前需完成/停止旧任务，并保留恢复所需旧 provider；不支持在途跨 provider 迁移。

`npm start -- .state/synthetic.sqlite` 仍提供开发用 stdin 虚构任务协议；它不代表真实业务职责。`npm run smoke` 使用配置模型进行无业务数据连通测试，临时会话库随验证清理。

### 对话附件与响应快照

消息支持最多 8 个服务器已上传附件；单件 20 MiB、合计 40 MiB。Node 只接受 UUID 和有界元数据，从固定 Django 内部端点按伙伴身份取回内容，不访问模型提供的 URL。PDF、Office、文本等解析由 Django 完成，读取状态与截断说明保留在附件元数据中。附件与交办原文合计 20000 字符的文字预算，超出部分标记为截断并保留原文件，不声称已读完整资料。提取文字以不可信资料加入模型上下文；图片以模型原生 image 块传入。公共历史仅返回用户原文、业务引用及附件元数据，不返回图片 base64、提取的文档全文、推理或工具参数。

`ASSISTANT_MODEL_SUPPORTS_IMAGES=false` 用于未配置视觉编码器的模型。图片仍可上传、保存与预览，模型会收到明确的未读取说明并继续文字任务；不能把存储成功描述为图片理解成功。启用视觉时设置为 `true`，并选择实际支持图片的服务和模型。

`GET /v1/partners/{id}/status` 提供 `deliveries` 的真实持久状态、`is_running`、`active_tasks`、以及 Pi 已提交的部分响应 `live_message` 和仅含名称/状态的 `live_tools`。前端轮询这些快照呈现实际生成进度，最终消息提交后替换临时内容。部分输出来自 Pi 的持久化节流提交，非客户端模拟逐字输出；进程恢复仍使用同一私有 SQLite 会话。
