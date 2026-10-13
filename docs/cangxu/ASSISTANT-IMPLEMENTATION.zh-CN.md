# 工作伙伴实施记录

日期：2026-10-13。对应 AI-01～AI-12，按技术交接 S0→S1→S2→S3→S4→S5 推进。本记录描述开发证据，不代表完整产品或现场业务验收。**当前交付见文末 assistant-ui 更新；前面的 S0/S1/S2 是阶段记录。**

## 当前决定

- 产品保持独立单列连续对话与右下角入口，后台常驻、事件/定时驱动、重启恢复进入第一版。
- 用户交办即为任务范围内的执行依据；系统自动形成后台凭据，不要求逐工具授权、重复批准计划或恢复时再次确认。长期职责设定一次后持续推进。缺失只阻塞依赖步骤，其他工作继续；本人检验、签字与业务审批保持原责任。
- 本地独立 Node 24 服务，Pi Durable、pi-ai、Chord 固定 `1.2.0`，用 npm lock 固定传递依赖。实际本机 Node `24.14.1`；不改动生产部署。
- 测试供应商为用户提供的自部署 OpenAI 兼容端点；初选 `GLM-5.3-Flash`，可配置供应商、地址、模型和凭据。金额预算不限，轮次、请求超时、重试及并发仍限制。仅发送虚构测试内容，生产资料范围与部署位置仍待落实。
- 凭据只存被 Git 忽略的 `src/assistant/.env.local`，文件权限为 `0600`。不写入源文件、锁文件、agent 文档或模型日志。

## S0：运行验证底座

实现位于 `src/assistant/`，运行步骤和边界见其 README：

- 真正的 Pi Harness、Node SQLite 持久存储与 durable task，不以浏览器轮询维持运行。
- 虚构业务事件及单次定时任务入列，稳定投递键去重、异参冲突检测；后台任务与回复停止分离。
- 指定任务/全部后台任务先持久冻结再取消；中断窗口与重启后仍检查冻结状态。
- SIGKILL 后重新打开同一存储，恢复原任务，仅写一次虚构完成标记。
- 单存储独占所有权，规范化符号链接路径，初始化失败释放占用。
- 可配置 OpenAI 兼容供应商，真实 Pi→模型→持久答案链路通过虚构连通测试。

S0 当时的边界：受信本地 stdin 协议，尚无 Django 身份网关；单次定时任务不等于持续职责周期调度。虚构完成标记不等于入库归档写入。SQLite 进程恢复不代表主机掉电、备份恢复或高可用。模型冒烟为单次无工具请求；货币不限额尚未接入费用归集。

## S1：模型与事务边界

实现位于 `src/backend/InvenTree/cangxu/assistant_models.py`、`assistant_services.py` 和迁移 `0017_assistant_foundation.py`：

- 部署/用户伙伴绑定、显式范围 grant、暂停/游标/下次运行时点职责、命令回执与最小 outbox 事件引用。
- 唯一用户绑定、伙伴内稳定命令键、有效期/版本约束、跨用户/伙伴引用校验；不增加库存余额或竞争性的消息正文。
- 内部事务原语重新读取当前用户、角色、绑定、grant 版本与有效性；稳定业务意图哈希不依赖恢复后的 run/step ID。
- 同键同参返回原回执；同键异参拒绝；业务数据库变更、回执及 outbox 同事务提交，异常全部回滚。
- 回执重查仍受当前身份/范围限制；未支持的数量限制不会被静默忽略。

S1 当时的边界：事务原语只接受宿主代码登记的 adapter，没有公开 HTTP 入口，也未给模型任意写入能力。测试 adapter 只更改虚构库位名称以验证事务。真实入库附件工具、现有入口事件覆盖、周期计划抢占/投递、服务身份认证、排他职责归属和自然语言交办自动登记仍待 S2。模型默认未配置/职责暂停是开发未接通状态，不能作为最终产品的逐动作确认流程。

## 验证证据

所有测试使用虚构数据。开发配置、数据库与附件放在 `/tmp/cangxu-assistant-test/`，未操作生产库。

| 检查 | 结果与范围 |
|---|---|
| `cd src/assistant && npm run check` | 通过，TypeScript |
| `cd src/assistant && npm test` | 4 项通过；后台事件/定时、去重、停止、SIGKILL 恢复、所有权与异常清理 |
| `cd src/assistant && npm run lint` | 通过，Biome |
| `cd src/assistant && npm run smoke` | 通过，GLM-5.3-Flash 返回虚构标记并生成持久答案 ID；临时会话库随后清理 |
| `npm audit` | 本次锁定依赖审计无已知漏洞；不是永久结论 |
| 后端模型与事务定向测试 | 16 项通过；模型约束、作用范围、撤权、角色移除、回执重试、异参冲突、事务回滚。测试合成 adapter，不等于入库工具验收 |
| 新迁移一致性、正反向验证 | 隔离 SQLite 库迁移到 0017 → 回退 0016 → 重应用 0017 均通过；`makemigrations cangxu --check --dry-run` 无差异。尚未验证生产升级和 PostgreSQL/MySQL 并发 |
| Ruff 与 `git diff --check` | 通过；新增后端文件格式检查通过 |
| CI | 未运行 |
| 业务隔离联调、现场验收 | 未执行 |

后端测试命令（本机缺少的原生依赖已安装 Pango/GLib）：

```sh
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib \
INVENTREE_CONFIG_FILE=/tmp/cangxu-assistant-test/config.yaml \
.venv/bin/python src/backend/InvenTree/manage.py test \
  cangxu.test_assistant_models cangxu.test_assistant_services --keepdb --noinput
```

## 后续阶段及需求状态

AI-02/03/04/07/08/09/12 已有局部工程底座及定向证据；全部 AI 需求仍未完成整体验收。IN-01～IN-06 的业务验收状态不因虚构运行实验改变。

下一阶段接通 Django 身份网关、后台交办凭据、实际入库查询/附件关联工具、事务 outbox 与 Django-Q2 周期补查，再完成 S3 无浏览器真实业务写入/响应丢失恢复；之后接 S4 简洁对话、全站入口、引用/附件、历史与重连。全流程正式知识、资料维护人、生产数据边界及备份恢复仍是交付工作，不缩减为只读聊天。

## 2026-10-13 S2 更新：先会查、能做、跑通链路

用户最新优先级已经同步到产品、技术和需求基线：先封装现有业务 API 为模型工具，再补网站与流程知识，不继续堆额外授权层。模型工具直接沿用伙伴绑定对应的当前登录用户和原业务权限，**不要求 grant**。旧的持续职责对象过滤记录只服务后台任务；命令回执只做幂等、恢复与审计。本人检验、实盘、签字、审批和正式放行仍走原流程。

### 当前实现

| 范围 | 实现与边界 |
|---|---|
| 模型工具 | Pi 真正注册 `business_query`、`business_capabilities`、`business_action`、`workflow_knowledge`；服务端身份来自伙伴绑定，模型不能传用户、任意 URL、SQL或shell |
| 业务查询 | 24类资源覆盖物料/SN、库存/库位、采购/收货/验收、工单/BOM、实装、质量返工、维修、交付、盘点和附件；原 API 权限与过滤规则生效，分页有界，未知过滤字段拒绝 |
| 业务执行 | 12种有限操作：采购收货、耗材领退料、安装/拆卸/替换、质量问题/返工登记、维修收送、签收登记、准备盘点、关联入库附件。固定端点和字段白名单，再由原序列化器与事务裁决；不是任意 CRUD |
| 执行一致性 | 原业务写入、命令回执及事件同事务；同键异参冲突。同一用户输入的同一规范化动作复用首个命令键，模型换 call ID 也不重复落账；新用户交办有独立意图 |
| 后台运行 | Django 持久接收队列；确认 Pi 持久接收后清除消息正文副本。伙伴传输租约保持输入顺序；职责周期槽、事件 fan-out、退避与确认持久保存；关闭浏览器不影响调度 |
| 入库附件 | 关联原附件记录，保留采购单及文件原归属，不复制文件；校验文件摘要、存在性和所属采购。原收货 API 可回查关联证据，回查不会冒充重新校验文件摘要。材料齐备与验收/正式归档完成区分；未知签字和处置保持等待 |
| 事件覆盖 | 普通收货/验收/反馈/处置 ORM 保存及原生采购附件与 outbox 同事务；bulk update、附件重新归属和单采购单超过500笔收货由职责周期补查覆盖；不宣称实时全入口零遗漏 |
| 停止 | 分回复、任务、全部自主写入和全部后台；任务先冻结再取消；停止写入后仍能只读检查和回查已提交回执 |
| 知识 | 10个业务/网站定位目录，带来源、版本、当前支持边界与正式资料缺口；这是实施指引，尚不是完整正式 SOP/网站手册。未实现 MCP server，当前使用 Pi typed tools |

新增主要文件：`assistant_business_tools.py` / `assistant_business_api.py` / `assistant_knowledge.py`、网关 API/队列/调度/事件模块、迁移0018～0021，以及 `src/assistant/src/model-tools.ts` / HTTP与常驻任务实现。所有开发数据均虚构，未部署或操作生产库存。

### 本轮验证

- Node：11项运行/协议/工具测试通过，TypeScript、Biome 通过。包括模型工具→接口→持久工具结果→回复、响应丢失换 call ID 仍复用原命令键、SIGKILL恢复、停止与通知去重。
- 后端定向业务工具：10项通过，逐个解析24条查询路由及各动作路由，验证当前权限、无 grant 调用、真实盘点准备、原生采购收货仅计库存一次、SN跨物料歧义、原序列化器拒绝与回执重试。补充归档回查后，业务工具与原收货 API 共19项定向测试通过。
- 后端组合回归：76项中75项通过，1项真实模型测试按设计默认跳过；覆盖新增模块、配置/领退料/维修/质量/盘点/交付原流程及附件。批量回归临时设置 `INVENTREE_THROTTLE_USER=none` 与 `INVENTREE_THROTTLE_ANON=none`，避免测试高速请求触发60/秒限流；生产限流未改，定向测试与真实模型联调使用正常设置。
- 真实自部署模型：单独启用 `CANGXU_LIVE_MODEL_TEST=1`，GLM-5.3-Flash 在真实 Pi 与 Django HTTP 服务间完成能力查询→查询库位→创建虚构盘点计划→按返回ID回查→持久回复，测试通过（约28秒）。数据库确认操作者、原生盘点记录与一份成功命令回执；没有填写实盘、检验、签字或审批。
- 无浏览器业务恢复：实际 Pi 子进程 + Django LiveServer，在后台任务入列后 SIGKILL，重启后只关联一次；另注入“业务提交后、响应到达前”中断，按原命令回执恢复，无重复附件关联。无变化定时检查没有重复消息。
- 迁移：空隔离库执行全部迁移，回退至0017并重应用0021通过，`makemigrations --check --dry-run` 无差异。此项不证明已有真实业务数据可无损降级；可空 grant 的新命令需要生产升级/备份恢复另验。
- API schema、最终 Ruff/格式及凭据隔离结果见下一条最终核对；CI未运行，现场业务验收未执行。

复现命令以 `.venv/bin/python src/backend/InvenTree/manage.py test ... --keepdb --noinput` 执行；日志分别为本机 `/tmp/cangxu-assistant-s2-full-regression.log`、`/tmp/cangxu-assistant-live-model-chain.log`、`/tmp/cangxu-assistant-s2-migration-schema.log`。本机测试需 `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib` 与隔离配置路径。

### 剩余交付工作

独立中文对话 UI、全站入口、附件与业务引用的前台交互、操作详情/未读状态、自然语言常驻职责管理、正式网站手册/SOP、资料治理与记忆管理、生产监控/预算归集、带真实数据的数据库/附件备份恢复与现场验收仍待完成。模型广泛写工具暂保留 Pi `replay: unsafe`；当前数据库幂等已经测试，不把未验证的插件或跨系统副作用宣称为安全重放。AI-01～AI-12 与 IN-01～IN-06 仍未完成整体验收。


最终核对：Ruff（新增模块及修改文件）、20个助手 Python 文件格式、TypeScript、Biome（12个 TS 文件）、`git diff --check` 均通过；凭据扫描确认模型 key 与服务 token 未出现在受跟踪或未忽略文件中，`.env.local` 为0600。schema 已生成，新增公开助手端点可见、内部工具端点隐藏；全库导出仍有 GenericMetadataView/SimpleGenericMetadataView 两类元数据错误汇总与新助手端点未提供 OAuth2 的提示，不能写成全库 schema 零告警。助手公共网关沿用会话、原生 API Token、Basic 登录；尚未传播 OAuth 委托范围，因此不接受 OAuth 凭据，避免把受限 token 提升为完整用户权限。生产部署、MCP OAuth、插件外部副作用与现场验收仍未执行。

## 2026-10-13 assistant-ui 更新：对话、图片与文件完整接线

用户明确选择 assistant-ui。此次实现关联 AI-01、AI-04、AI-06～AI-10、AI-12；业务附件关联还关联 IN-05。这些是本地开发证据，仍不代替现场业务验收。

### 实现范围

| 范围 | 已实现 |
|---|---|
| 对话界面 | `@assistant-ui/react 0.15.28`、`@assistant-ui/react-markdown 0.14.22`、ExternalStoreRuntime、真实 primitives 与 AttachmentAdapter；独立单列 `/assistant/`、桌面/移动导航与右下角入口，使用原 Mantine 主题；标准网站部署前缀下实际地址为 `/web/assistant/` |
| 消息体验 | 连续历史、分页、已加载历史查找、时间、复制、Markdown 表格/代码块、滚动到底部；按需菜单停止回复/自主写入/后台工作；处理中可继续向 Pi 持久 inbox 补充消息，无额外授权弹窗 |
| 附件体验 | 文件选择、粘贴、拖放、进度、失败原因、移除、认证下载、图片缩略图和放大预览；上传按输入框排队，暂时失败复用原上传键有限重试；未发送文字和附件按 API 主机及本人保存为浏览器草稿，刷新核验附件归属后恢复，不自动发送 |
| 业务引用 | 从物料、库存、库位、采购单、工单、销售单及发运详情进入时带可移除引用；原 API 验证当前用户和对象，服务端生成名称/链接，投递前重新核权；已移除引用刷新后不恢复 |
| 真实响应 | 轮询 Pi 已持久提交的部分文本和任务状态，最终消息落库后替换临时内容；不使用模拟逐字输出，不声称已经实现 SSE/WebSocket；后台待投递和失败状态可回查，同请求显式重试不重复交办 |
| 私有存储 | Django 迁移0022/0023；UUID 与伙伴绑定隔离，下载/预览均经过原登录身份；文件在公共 MEDIA_ROOT 之外，没有匿名文件 URL；草稿可删除，已发送或转入业务的文件禁止作为草稿删除 |
| 模型输入 | PNG/JPEG/WEBP/GIF 为真实图片块；PDF、DOCX、XLSX、CSV/TSV、UTF-8 TXT/MD/JSON/LOG 为实际提取内容。读取失败、截断或视觉不可用保留说明；历史不公开 base64、提取全文、推理或凭据 |
| 正式业务附件 | 新增第13种有限动作 `attach_chat_file`：本人聊天文件→原生 Attachment multipart API→返回正式附件ID→`link_receipt_archive`→原收货 API 回查。支持原生确实允许挂附件的7类对象，复用原权限/操作者/事务/命令回执；不会因聊天上传自动归档或代替检验、签字、批准 |
| 并发与恢复 | 修复 SQLite 多附件同时上传的 writer 竞争；有限忙锁重试，耗尽返回可重试503；失败清理文件，同上传键不重复保存；内部 RuntimeTransport 使用直接连接，避开系统代理探测及 macOS fork worker 中相应风险 |

文件限制：每次最多8个，单件20MiB、总计40MiB；图片最多2000万像素。Office 展开限制40MiB/2000项；XLSX提取最多每表10000行、100列，PDF最多300页。模型输入中文字与本轮交办合计20000字符，超出明确说明并保留原件。图片供模型使用时纠正EXIF方向、透明底转白、取首帧并缩至2048像素；原图下载保留原件。

### 本地验证与 QA

Browser 插件未提供，按前端验证技能使用项目 Playwright。组件测试为虚构 HTTP 数据；下面的实际网站联调使用真实 Django、Django-Q、Pi 和用户提供的 GLM 服务，资料仍全部虚构。

| 检查 | 结果与证据 |
|---|---|
| 后端组合 | 64项中63通过，真实模型专项默认跳过1项；随后网关含直接连接回归11项通过。覆盖权限/隔离、MIME/文件限制、模型真实内容、归档推广、幂等/回滚、四线程上传、失败文件清理、恢复和停止。批量测试仅当前进程关闭限流，生产配置未改 |
| Node | 12项通过，TypeScript/Biome通过；实际 OpenAI 协议图片请求、真实部分输出、私有历史与重启、文字预算和40MiB总量限制均有断言 |
| 前端交互 | 5项 Playwright 通过；图片预览、同键发送/上传重试、390px暗色、草稿与引用、停止、处理中补充、粘贴/拖放、排队取消后续传均覆盖 |
| 实际网站与模型 | 原登录、普通虚构登录用户（非超级用户）、上传CSV和PNG、图片放大、发送、后台实际提取、GLM返回 `SYNTHETIC_SUM=5`（2+3）、按本次请求ID确认持久用户消息及回复、刷新回查两份附件，均通过；没有改业务记录 |
| 页面/截图 | `http://localhost:5173/web/assistant/`，1440×1000及390×844；页面主体非空、无框架错误覆盖层、无横向溢出。最终控制台仅初始未登录会话探测401，无应用脚本错误；图片卡片说明挤压已在真实手机宽度复核后修正 |
| 构建/迁移/schema | 前后端类型/静态检查、Vite生产构建、0022/0023隔离库升级、`makemigrations --check`通过；新增附件/状态端点进入schema，内部内容接口隐藏。全库仍为23条错误（2类元数据错误）及1类OAuth提示，不宣称零告警；构建仍有大chunk提示 |
| 凭据 | 模型key与服务token扫描受跟踪及未忽略文件无匹配，忽略的`.env.local`为0600。未提交commit、未创建PR、未部署生产；CI和现场验收未执行 |

可复现组件测试：在`src/frontend`的Vite服务启动后，以只包含该spec、baseURL及Chromium的Playwright配置运行`tests/pui_cangxu_assistant_component.spec.ts`。完整站点采用正常登录与原权限；组件入口位于`tests/fixtures/cangxu-assistant-smoke.html`，不属于生产路由。测试报告/截图放在本机`/tmp`，不提交测试运行产物。

证据日志：`/tmp/cangxu-assistant-ui-final-backend.log`、`/tmp/cangxu-assistant-ui-gateway-final.log`、`/tmp/cangxu-assistant-ui-final-node.log`、`/tmp/cangxu-assistant-ui-playwright-final.log`、`/tmp/cangxu-assistant-live-browser.log`、`/tmp/cangxu-assistant-capture.log`、`/tmp/cangxu-assistant-mobile-default.log`、`/tmp/cangxu-assistant-ui-build-final.log`。实际站点截图为`/tmp/cangxu-assistant-live-{desktop,mobile,preview}.png`。

### 当前边界

自部署 GLM 服务真实返回“未启用视觉编码器”，本地已设`ASSISTANT_MODEL_SUPPORTS_IMAGES=false`：图片上传、保存、预览、下载和归档可用，当前服务不能识图；支持视觉的实际模型/编码器启用后设为true，图片协议链路已有独立实测。扫描PDF暂无OCR，DOCX/XLSX当前提取文字/单元格，不提取嵌入图片或执行公式；旧DOC/XLS、加密及未支持格式明确拒绝。

聊天草稿是同浏览器、同用户、同API主机的sessionStorage草稿，不是跨设备同步。对话及登录流程在小屏直接可用；原移动提示增加工作伙伴入口，返回其他业务页后仍按原移动策略显示提示。最初小屏联调使用`mobile_mode=allow-always`，最终另验证不覆盖此配置时的手机登录、对话、业务页提示和返回入口。历史查找仅搜索已加载消息。正式SOP/知识治理、记忆管理、生产监控/预算、OAuth委托范围、MCP服务、跨系统副作用、现场业务验收仍待完成。

生产备份必须同时包含Django数据库、原MEDIA_ROOT、Pi SQLite持久目录和`ASSISTANT_ATTACHMENT_ROOT`（默认MEDIA_ROOT父目录下`assistant-private`），不能只备份原媒体目录。未发送且用户未主动移除的私有文件暂保留；留存期限、无主文件清理、全量备份恢复与升级回滚需部署验收。macOS本地Django-Q仍观察到个别worker重生，原因未全部定位，助手队列最终恢复并完成真实请求；本轮不构成长时间进程稳定性证明。
