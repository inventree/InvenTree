# 仓序 · Cangxu

面向智算服务器制造的仓储、装配与追溯系统，基于 [InvenTree](https://github.com/inventree/InvenTree) 开发。

[业务需求与验收](docs/cangxu/REQUIREMENTS.zh-CN.md) · [改造规划](docs/cangxu/ROADMAP.zh-CN.md) · [行业数据模型设计](docs/cangxu/DOMAIN-MODEL.zh-CN.md) · [上游 README](README.upstream.md) · [MIT 许可证](LICENSE)

## 当前状态

2026-10-09 已依据实际生产、交付、售后和入库场景整理[业务需求基线](docs/cangxu/REQUIREMENTS.zh-CN.md)，明确可复用能力、待补功能、验收条件及待确认规则。当前优先完成业务闭环，再深化完整拓扑与智能体能力。

仓序目前处于 fork 与设计阶段。本次新增中文项目说明和智算服务器行业改造规划，尚未实现行业扩展或 Pi 智能体，也未完成工厂生产验证。应用内名称和图标、包名及镜像仍沿用 InvenTree；本仓库暂无仓序专用安装包或镜像。

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
| 智能体 | Pi + 模型服务、知识检索、实时库存查询、缺料分析和业务草稿 |

硬件型号、规格及兼容规则以实际供应商资料和工程签核为准。项目不绑定某一家 GPU 厂商，也不预设所有服务器采用同一种拓扑。

## 实现方向

保留 InvenTree 的物料、库存和工单主数据，通过 Django 行业扩展补充槽位、端口、连接关系及配置版本。优先配置和复用原版页面，针对实际操作障碍增加界面。

Pi 通过受权限约束的业务工具访问系统；库存数量、预留和操作结果以业务数据库为准。向量检索用于手册、规范和故障案例，设计上优先评估 PostgreSQL + pgvector。

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
