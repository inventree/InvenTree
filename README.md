# 仓序 · Cangxu

面向智算服务器制造的仓储、装配与追溯系统，基于 [InvenTree](https://github.com/inventree/InvenTree) 开发。

[业务需求与验收](docs/cangxu/REQUIREMENTS.zh-CN.md) · [改造规划](docs/cangxu/ROADMAP.zh-CN.md) · [行业数据模型设计](docs/cangxu/DOMAIN-MODEL.zh-CN.md) · [上游 README](README.upstream.md) · [MIT 许可证](LICENSE)

[工作伙伴产品规划](docs/cangxu/ASSISTANT-PRODUCT.zh-CN.md) · [工作伙伴技术规划与实施交接](docs/cangxu/ASSISTANT-TECHNICAL.zh-CN.md)（2026-10-13：规划已整理，功能待实现与验收）

## 当前状态

截至 2026-10-12，开发分支已实现首批行业数据模型、REST API、合成数据扩展，以及耗材领退料和发货签收/差异处理中文界面。演示目录包含 GPU、PCIe/NVLink、以太网/InfiniBand Switch、Retimer、GPU 供电线束、MCIO、DAC/AOC、多分支线缆等类型；另有 Broadcom PEX89048、Microchip Switchtec PM50100B1-FEI 与联瑞 LR-LINK LRSV9500-4I 的公开型号草稿。公开厂商资料只用于演示制造商、芯片和成品板卡的不同角色；仓序 IPN 为虚构值、这些新型号没有演示库存，规格草稿未经本公司工程核验，不代表实际采购、兼容或生产放行。

当前功能仍处于开发和隔离开发库集成验证阶段，不代表生产验收。试点库存唯一业务账已确认由 InvenTree/仓序承担，ERP 不并行回写库存余额；源工作簿未上传或原样导入。完整 PCIe/GPU 拓扑、工程兼容规则、收货与售后专用表单、客户现场扫码和备份恢复验证仍未完成。签收界面通过生产构建及隔离组件浏览器测试，真实发货页面和后端联调仍待验收。应用内名称和图标、包名及镜像仍沿用 InvenTree；本仓库暂无仓序专用安装包或镜像。

已核对的上游基线：`9bc5054d8`（2026-09-07，`master`）。这是开发分支；生产试点前需要选择并验证稳定版本。

## 可复用的上游能力

- 物料分类、规格参数、供应商、采购收货和库位管理。
- 批次与序列号库存、BOM、装配工单、替代物料和单机配件关联。
- 配件安装与拆回仓库，保留相关库存操作记录。
- 单机测试结果、附件、测试站与测试时间；可配置必测项目通过后才能完工。
- 盘点及库存调整、销售与退货相关功能。
- React Web 界面、简体/繁体中文翻译、REST API 和插件机制。

上述能力是上游源码确认结果，现场工作流仍需验收。阻止未通过必测项目的成品完工、退货界面等功能需要检查并启用相应配置。

## 智算服务器改造范围（规划）

| 领域 | 计划覆盖 |
|---|---|
| GPU 与整机 | GPU 型号/显存/形态、加速底板、单机 SN、GPU UUID、装机位置及配置版本 |
| PCIe | CPU/Root Complex、PCIe Switch、Root/Upstream/Downstream Port、Riser、Retimer、插槽与链路 |
| GPU 互联 | NVLink/NVSwitch 等互联类型、端口、拓扑和检测结果，按实际平台建模 |
| 网络 | NIC/HCA/DPU、以太网/InfiniBand 交换机、端口、光模块及网络互联 |
| 线缆 | GPU 供电线束、内部 PCIe 高速线、互联线、DAC/AOC/有源铜缆、光纤及 breakout 分支 |
| 配套部件 | CPU、DIMM、NVMe/背板、PSU/PDB、风扇/散热器、液冷部件、机箱/机柜与附件 |
| 生产质量 | 槽位和端点核验、工程批准的兼容规则、测试证据、换件复测、交付配置快照 |
| 常驻工作伙伴 | Pi Durable + 简洁独立对话页、全流程知识、实时查询、事件/定时驱动与授权业务执行 |

硬件型号、规格及兼容规则以实际供应商资料和工程签核为准。项目不绑定某一家 GPU 厂商，也不预设所有服务器采用同一种拓扑。

型号样例的公开来源：[Broadcom PEX89048](https://www.broadcom.com/products/pcie-switches-retimers/expressfabric/gen5/pex89048)、[Microchip Switchtec PFX Gen5](https://ww1.microchip.com/downloads/aemDocuments/documents/DCS/ProductDocuments/Brochures/00003776D.pdf)、[LR-LINK LRSV9500-4I](https://www.lr-link.com.cn/productshow/LRSV9500-4I.html)。这些来源不证明该型号已进入本公司的采购或生产清单。

## 实现方向

保留 InvenTree 的物料、库存和工单主数据，通过 Django 行业扩展补充槽位、端口、连接关系及配置版本。优先配置和复用原版页面，针对实际操作障碍增加界面。

Pi Durable 规划为独立常驻服务，关闭网页后仍能处理已授权的事件与定时工作；前台以简洁连续对话为中心，右下角提供轻量入口。它通过受权限约束的业务工具访问系统；库存数量、预留和操作结果以业务数据库为准，任务恢复不替代业务幂等。知识检索用于手册、规范和故障案例，候选 PostgreSQL + pgvector 只作可选索引。以上助手能力目前均待实现。

## 开发与试用

当前源码的环境搭建、测试和贡献约定见 [CONTRIBUTING.md](CONTRIBUTING.md)。

- [上游安装文档](https://docs.inventree.org/en/stable/start/)
- [上游公开演示](https://demo.inventree.org/)：演示 InvenTree 原版能力，不包含仓序规划功能。
- [上游 API 文档](https://docs.inventree.org/en/stable/api/)

正式试点前需要准备实际 BOM、标签、扫码与打印设备、测试报告样例，并验证备份恢复、权限和并发库存操作。

## 来源与许可

仓序是 InvenTree 的独立衍生项目。感谢 InvenTree 开发者与贡献者提供的基础能力。

本项目保留上游 Git 历史、原始 README 和 MIT 许可证，包括 `Copyright (c) 2017 - InvenTree Developers`。新增文档同样采用 MIT 许可证。上游名称、商标和第三方组件的权利仍归各自权利人；本项目不表示获得上游或硬件厂商背书。

行业改造计划由本 fork 维护。向上游贡献时遵守其 [AGENTS.md](AGENTS.md) 和 [贡献规范](CONTRIBUTING.md)。
