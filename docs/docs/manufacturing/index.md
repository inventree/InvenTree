---
title: Manufacturing
---

## Manufacturing

InvenTree offers a comprehensive and flexible manufacturing system designed to streamline production workflows, manage inventory consumption, and track build progress in real-time. It is ideal for organizations looking to manage in-house manufacturing, sub-assemblies, and production lines with high visibility and control.

### BOM Support

InvenTree provides comprehensive multi-level BOM (Bill of Material) support, allowing users to define complex assemblies with multiple sub-components. BOMs can be created and managed directly within the InvenTree interface, enabling users to easily track the components required for each assembly.

Read more about BOM management in the [BOM documentation](./bom.md).

### Build Orders

Build orders are used to manage the manufacturing process, allowing users to create and track production runs for specific assemblies. Each build order is linked to a specific BOM, ensuring that the correct components are consumed during the manufacturing process.

Read more about build orders in the [Build Order documentation](./build.md).

### Stock Allocation

InvenTree allows users to allocate stock items to specific build orders, ensuring that the required components are reserved for production. This helps to prevent stock shortages and ensures that the right parts are available when needed.

Read more about stock allocation in the [Stock Allocation documentation](./allocate.md).

### Disassembly

The reverse process is also supported - an assembled stock item can be broken back down into its component parts, based on its BOM. This is useful for reworking or scrapping an assembly, or for splitting a bundled "kit" product purchased from a supplier into its individual components.

Read more about this process in the [Stock Disassembly documentation](../stock/disassemble.md).
