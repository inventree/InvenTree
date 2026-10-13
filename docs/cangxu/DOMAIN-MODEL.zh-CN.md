# 智算服务器行业数据模型设计

日期：2026-09-07；实施状态更新：2026-10-12。状态：基础追溯模型与硬件规格修订/端口/线缆端定义已进入开发分支；新增来料验收记录、异常反馈和处置审批表；完整硬件拓扑、兼容规则和工程放行仍是候选设计。配合 [改造规划](ROADMAP.zh-CN.md) 和[业务需求基线](REQUIREMENTS.zh-CN.md)阅读。

## 1. 建模原则

物料型号使用上游 `Part`，具体实物使用 `StockItem`，装配需求使用 `BomItem`/`BuildLine`，单机产物使用 `StockItem` 与 `BuildItem.install_into`。行业扩展表达技术规格、位置、端点和有版本的关系，不重新创建库存余额。

区分四层：型号规格 → 设计配置 → 实际装机 → 自动检测观测。采购规格、现场安装和检测结果可以不同，差异必须显式处理。

`switch` 必须具有类别：PCIe Switch、NVSwitch/其他加速互联交换组件、Ethernet Switch、InfiniBand Switch。逻辑端点和芯片不一定能独立入库；焊接芯片可作为所属板卡的拓扑节点，独立 FRU 才关联独立库存实物。

PCIe、NVLink、Ethernet/InfiniBand、供电和液冷连接采用不同关系类型。GPU 不预设为 PCIe 插卡；支持模块/底板式安装。服务器内部可固定互联，不强行为每条逻辑链路创建一根库存线缆。

## 1.1 当前分支已实现的基础模型

`src/backend/InvenTree/cangxu/models.py` 与迁移实现了编码别名、制造批次及 PCB/SMT/板卡制造商/芯片厂商/供应商等伙伴角色、单机配置版本、配置实装项、配置测试证据、换件记录、质量问题与返工任务、服务单与保管事件、盘点会话及发货清单。批次关联原生采购单明细；客户退货可引用原生销售发货单。它们引用 InvenTree 的 Part、StockItem、Build、PurchaseOrderLineItem、SalesOrderShipment 和用户记录，不建立第二套库存余额。

新增 `HardwareProfileRevision` 将技术类别、协议、物理形态、芯片厂商、板卡制造商和带单位来源规格关联到现有 Part，并以草稿/批准/被替代状态管理修订；`HardwarePortDefinition` 描述版本化端口，`CableEndDefinition` 支持多分支线缆端和映射。PCIe、NVLink、Ethernet、InfiniBand 交换部件使用不同类型；GPU 形态与协议独立。API 仅允许编辑草稿，批准时要求工程来源、switch 端口或线缆端定义。

入库归档表包括 `PurchaseReceiptInspection`（检验方式、抽样数、型号/数量/包装/外观结论、检查人和双方签字）、`PurchaseReceiptFeedback`（技术支持/采购的反馈往返）和 `PurchaseReceiptDisposition`（正常/让步/退回及审批证据）。`PurchaseReceipt` 复用 InvenTree 附件混入能力，照片与验收单使用上游 Attachment 并能关联单次收货。收货库存状态可选隔离，默认可用；异常验收会转入隔离待处置，通过一次批准/驳回后完成正常/让步/退货。迁移已应用，pro6000D API 回归覆盖验收、异常反馈/处置、默认收货异常后的隔离、退货库存去向以及附件上传检索；Chromium 中文组件测试覆盖全检表单、签字和提交（API 使用虚构夹具）。真实 Django 页面/API 联调和现场验收仍待验证。报告号目前按收货记录 ID 生成 `IN-########`；抽样方案和附件保留期仍按需求基线待确认，技术/采购反馈不阻塞处置。

以上不是完整拓扑：平台槽位、实装端口、连接/链路实例、版本化兼容规则、测试计划和正式放行记录尚未实现。演示中的交换厂商角色和示例规格不是实际产品或兼容性资料。

## 2. 行业物料目录与参数（优先复用上游分类/参数模板）

| 类别 | 必要规格字段（按类别适用） | 实物/追溯 |
|---|---|---|
| GPU/加速器 | 厂商、型号、显存容量/类型、形态、主机接口、功耗/散热、模块与底板匹配 | SN、内部资产号；GPU UUID 为观测标识 |
| GPU 底板/加速托盘 | 平台/板卡版本、支持模块、安装位、供电/散热要求 | 整板 SN 与子部件关系 |
| PCIe Switch 板/芯片 | 型号/版本、协议代际、上/下行端口及通道配置 | FRU 板卡 SN；板载芯片作为组件节点 |
| NVSwitch/加速互联组件 | 互联类型、版本、端口定义、平台适配 | 所属底板/托盘或独立 FRU |
| Riser/Retimer/转接板 | 接口、机械尺寸、电气通道、代际、支持模式 | 独立 FRU 可有 SN/批次 |
| NIC/HCA/DPU | 类型、协议、端口形态/速率、PCIe 接口、固件约束 | SN、MAC/GUID 等观测标识 |
| 网络交换机 | Ethernet/InfiniBand、端口/拆分模式、风向、供电 | 设备 SN、端口与上架位置 |
| 光模块 | 两侧接口、介质、波长、速率/通道、厂商料号及兼容声明 | SN 或批次；模块与光纤分开 |
| DAC/AOC/有源铜缆/光纤 | 介质、长度、端点数量/接口、分支映射、额定模式、方向/极性（适用时） | 线缆实例/批次；实际接线端点 |
| GPU 供电线束 | 两端/多端连接器、厂家针脚定义、额定电流/功率、线规、方向 | 料号/版本、批次或实例 |
| 内部高速线/互联桥 | 协议、接口、长度、通道映射、平台限制 | GPU/PCIe 相关线与供电线分开管理 |
| CPU/DIMM | 插座/代际、核心或容量、频率、电气类型、功耗 | SN 或内部编号、槽位 |
| NVMe/HDD/背板/控制卡 | 协议、形态、容量、背板通道/接口 | 盘位、SN、背板/控制卡关系 |
| PSU/PDB/供电组件 | 功率、电压/电流、输入/输出接口、冗余方案 | SN、供电域与连接 |
| 散热/液冷组件 | 散热器、风扇、冷板、分水器、接头/管路规格及平台适配 | 批次/实例、连接与泄漏测试 |
| 机箱/机柜/PDU/附件 | 尺寸/U 位、承重、安装方向、供电、导轨/固定件 | 整机/机柜位置及附件清单 |

参数必须记录单位、数据类型、来源和版本。参数模板适合展示与导入；参与强制约束、关联、唯一性或频繁查询的字段进入结构化扩展模型。实际适配清单由工程人员批准，不根据名称相近或连接器外观推断。

## 3. 拟新增实体与关系

以下主键统一使用稳定 ID，引用上游对象采用外键；外部标识不替代内部主键。所有更改包含操作者、时间和业务单据来源。

| 实体 | 关键字段 | 关系/用途 |
|---|---|---|
| `HardwareProfileRevision` | part、revision、kind、protocol、form_factor、chip_vendor、board_manufacturer、specifications、source_reference、state | 已实现模型/API；Part 1:N 草稿/批准修订，批准后不可变 |
| `PurchaseReceiptInspection` | receipt、report_number、sampling_method、sampled_quantity、inspection_results、signatures、state | 已实现表结构；对单次收货记录检验与签字，不直接创建库存余额 |
| `PurchaseReceiptFeedback` | inspection、department、message、response、created_by、responded_by | 已实现表结构；记录技术支持与采购的异常反馈往返 |
| `PurchaseReceiptDisposition` | inspection、outcome、state、requested_by、approved_by、approval_notes | 表结构、API 和单步批准/驳回状态已实现；技术/采购反馈为可选记录，不阻塞处置 |
| `PlatformRevision` | assembly_part、revision、status、approved_by | 定义机型与拓扑模板的工程版本 |
| `SlotDefinition` | platform_revision、path、slot_kind、mechanical_spec、electrical_spec、capacity | 设计槽位，例如 GPU0、DIMM_A1；机械与电气能力分离 |
| `HardwarePortDefinition` | profile_revision、path、protocol、connector、supported_modes、lane_count | 已实现模型/API；设计端口，形态不直接决定协议/速率 |
| `ConfigurationRevision` | unit_stock_item、revision、state、base_platform、bom_snapshot、parent_revision | 单机计划/实际/交付版本，正式版本冻结 |
| `Installation` | configuration、component_stock_item、slot_path、installed_at、removed_at、source_build_item | 有效装机位置；与上游 belongs_to 在同一业务操作内保持一致 |
| `DeviceIdentifier` | stock_item、namespace、value、observed_at、source | SN/MAC/GUID/GPU UUID/BDF 等带范围标识 |
| `TopologyNode` | configuration、kind、stock_item?、parent_node?、local_path | Root Complex、Switch 芯片、GPU 等；无独立 FRU 可不关联库存 |
| `PortInstance` | node、definition、path、configured_mode、state | 实际端口及模式；路径在节点内唯一 |
| `TopologyEdge` | configuration、a_port、b_port、fabric_kind、lane_map、provenance | 设计/实际固定或可拆逻辑链路；记录 CPU/NUMA 归属 |
| `CableAssemblySpec` | part、revision、medium、length、ratings、source | 线缆型号及工程版本 |
| `CableEndDefinition` | profile_revision、end_label、connector、protocol、branch_group、lane_map、pinout_reference | 已实现模型/API；一根线允许两个以上端头 |
| `CableInstance` | stock_item、cable_spec、internal_label | SN 或内部编号；每根需追踪的实物对应实例 |
| `CableEndInstance` | cable_instance、end_spec、label | 实际线头 A/B1/B2/B3/B4 等 |
| `Connection` | configuration、cable_end、port、connected_at、disconnected_at、verified_by | 每个端头接到哪个端口；一个物理插口只允许一个有效连接 |
| `CompatibilityRuleRevision` | scope、predicate、severity、evidence、approved_by、version | 型号/固件/端口模式/电气条件的工程批准规则 |
| `FirmwareBaseline` | platform_revision、component_selector、firmware_type、version_constraint、source | BIOS/BMC/GPU/NIC/Switch 等版本组合的基线 |
| `InspectionRun` | unit、configuration、collector_version、observed_at、raw_attachment、status | 导入硬件、固件、拓扑检测结果，保留来源 |
| `ObservedComponent/Link` | inspection、identifier、observed_specs、matched_object? | 自动检测不直接改写实际装机；无法匹配形成差异 |
| `ConfigurationDiscrepancy` | expected、observed、kind、owner、resolution | 缺件、错位、链路降速、固件不符等差异闭环 |
| `TestPlanRevision` | platform、required_templates、limits、environment、version | 规定应运行的测试、阈值与环境 |
| `TestExecution` | configuration、plan_revision、station、environment、result_refs、validity | 引用上游 StockItemTestResult，绑定配置版本与软件环境 |
| `ReplacementRecord` | unit、old_item、new_item、reason、before_revision、after_revision、return_location | 换件事务与旧件去向；触发相关测试失效 |
| `ReleaseRecord` | configuration、test_plan、evidence_refs、approved_by、shipment_ref、manifest_hash | 交付快照、批准与可核验配置清单 |
| `CountSession/CountLine/DiscrepancyCase` | scope、baseline_time、counted_by、evidence、review_state | P0 确认缺口后新增；最终调整复用库存接口 |

`ConfigurationRevision` 的状态拟为 draft → validated → released → superseded；旧版本和旧测试证据保留。正式版本的更正创建新版本或冲正事件，不能就地改写交付历史。

## 4. 必须落地的约束

1. 同一实物在同一时刻只能归属一台直接父装配；父子层级不能成环。多槽宽 GPU 的占位通过一组槽位占用表示，不能只检查主插槽。
2. 槽位唯一性按整机/配置有效期检查。历史配置允许引用同一旧件；不能把历史记录误判成当前重复占用。
3. 制造商 SN 的唯一范围需定义厂商/料号；系统内部标签全局唯一。PCIe BDF 是一次主机观测中的地址，可因配置变化而改变，不能当永久实物 ID。
4. 端口具备独立的物理形态、协议、速率和通道模式。PCIe 机械 x16 与电气通道数分开；期望最大能力与实测协商结果分开。
5. breakout 是一个库存线缆实例加多个端头及映射；不能把它拆成多条独立库存线，也不能简单限制为 A/B 两端。
6. 光模块插入设备笼位，光纤接模块光口；DAC/AOC 集成端头按对应物料类型处理，避免重复统计光模块。
7. 固定板级互联属于拓扑关系，可没有线缆实例；NVSwitch、PCIe Switch、网络交换机使用各自端口类型，不能互换。
8. GPU 供电规则需要厂家批准的针脚定义与额定值；不能根据“接口插得上”判定兼容。液冷连接同样需要独立的介质和接口规则。
9. 替代料可用须同时满足 BOM 允许集合和版本化工程约束。未知参数返回待验证，不能自动视为通过。
10. 换件/重接线/固件变更创建配置版本，并使受影响测试失效；测试通过必须属于当前应验配置，不能沿用旧配置的通过记录。
11. 安装与拆卸同时更新上游库存关系、行业位置/连接和历史；事务失败全部回滚。重复幂等键同参返回原结果，异参拒绝。
12. 交付检查 BOM/实物/槽位/接线/必测/未结差异；阻断项通过后生成不可变清单，返修创建新分支记录并保留原交付证据。
13. 软删除或引用保护用于关键追溯实体；保留规则与上游级联删除行为需逐项审计。正式单机档案不能因删除一个物料模板而丢失。
14. 规则校验必须执行在后端，并定义人工豁免权限、理由、有效期和审计；界面和智能体不能绕过约束。

## 5. GPU/拓扑检测与测试集成

先定义采集结果格式和导入接口，再逐个适配厂商工具。可评估的来源包括 Redfish/BMC 清单、PCIe 枚举、GPU 管理工具、交换机/网卡信息以及工厂测试平台。采集器采用只读权限，结果含原始文件、采集时间与工具版本；错误、部分结果与离线状态显式保留。

拟覆盖检测：配件身份与数量、槽位归属、PCIe 代际/宽度、互联可达性、固件组合、功耗/温度、GPU 显存与计算测试、网络链路与通信测试。验收阈值由机型工程规范确定；应用版本、驱动、测试负载与环境必须随结果保存。

这些工具/协议适配均尚未实现；非 NVIDIA 平台通过新的采集适配器和 profile 扩展，业务模型不硬编码某家厂商命令。

## 6. 第一组验收样例（虚构，不是兼容性承诺）

- 样例 A：CPU Root Complex → PCIe Switch → 多张 PCIe GPU，另有 NIC；包含 Riser、内部高速线和 GPU 供电线束。
- 样例 B：模块式 GPU 底板与加速互联交换组件，另有 HCA → 外部网络交换机；包含光模块和一分多线缆。
- 两例均配置两台整机、部分相同料号不同 SN 的配件；一次同 SN 并发安装、一次错误接线、一次换件、一次复测与返修。
- 必须验证：实物数守恒、两例拓扑可表达、所有连接端头可追踪、旧配置可重建、错误操作被明确拒绝。

## 7. 技术验证与迁移策略

先用独立 Django 插件/App 原型验证自定义模型、外键、权限映射和迁移；模板与实例分开建表。若扩展点无法可靠拦截核心写操作，再评估最小核心补丁，禁止用易失的异步事件充当库存事务保证。

模板导入采用稳定业务键和版本，重复导入不重复生成实例；新增索引与唯一约束先在 PostgreSQL 并发测试中验证。所有模型提供可审查的 API schema、迁移与回滚/恢复步骤。

Pi Durable 通过业务模型提供的精确查询、差异分析及授权操作工具访问系统；知识索引带对象权限、来源/版本与失效机制，索引可重建。自然语言推测不能直接生成正式兼容规则或库存事实。2026-10-13 规划允许常驻运行与知识底座并行建设，具体写动作仍依赖业务规则与验收；会话、授权、事件、命令回执及恢复方案见[助手技术规划](ASSISTANT-TECHNICAL.zh-CN.md)，不得另建库存余额。

## 8. 参考依据与待确认项

上游源码路径与基线见 [改造规划](ROADMAP.zh-CN.md)。以下官方资料用于确认硬件概念的区分，不代表所有智算服务器采用对应平台结构：

- [NVIDIA DGX H100/H200 平台与拓扑](https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html)：PCIe、GPU 互联与网络连接属于不同结构。
- [NVIDIA LinkX 线缆概念](https://docs.nvidia.com/networking-ethernet-software/knowledge-base/Setup-and-Getting-Started/layer-1-Data-Center-Cheat-Sheet/)：区分 DAC/AOC 与可插拔光模块、光纤。
- [NVIDIA 线缆管理定义](https://networking-docs.nvidia.com/cablemanagfaq/cable-and-connector-definitions)：线缆与连接器术语。

实施前待确认：实际 GPU 厂商/形态、机型数量、Switch 所指设备清单、是否整柜交付、具体线缆/接头料号、哪些部件逐件追踪、工程兼容表来源、测试平台与放行责任人。
