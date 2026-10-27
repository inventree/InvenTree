import { registerModelRenderers } from '@lib/enums/ModelInformation';
import { ModelType } from '@lib/enums/ModelType';
import { RenderBuildItem, RenderBuildLine, RenderBuildOrder } from './Build';
import {
  RenderAddress,
  RenderCompany,
  RenderContact,
  RenderManufacturerPart,
  RenderSupplierPart
} from './Company';
import {
  RenderContentType,
  RenderError,
  RenderImportSession,
  RenderParameter,
  RenderParameterTemplate,
  RenderProjectCode,
  RenderSelectionEntry,
  RenderSelectionList,
  RenderTag
} from './Generic';
import { RenderNoteTemplate } from './Note';
import {
  RenderPurchaseOrder,
  RenderReturnOrder,
  RenderReturnOrderLineItem,
  RenderSalesOrder,
  RenderSalesOrderShipment,
  RenderTransferOrder,
  RenderTransferOrderLineItem
} from './Order';
import { RenderPart, RenderPartCategory, RenderPartTestTemplate } from './Part';
import { RenderPlugin } from './Plugin';
import { RenderLabelTemplate, RenderReportTemplate } from './Report';
import {
  RenderStockItem,
  RenderStockLocation,
  RenderStockLocationType
} from './Stock';
import { RenderGroup, RenderOwner, RenderUser } from './User';

registerModelRenderers({
  [ModelType.address]: RenderAddress,
  [ModelType.build]: RenderBuildOrder,
  [ModelType.buildline]: RenderBuildLine,
  [ModelType.builditem]: RenderBuildItem,
  [ModelType.company]: RenderCompany,
  [ModelType.contact]: RenderContact,
  [ModelType.parameter]: RenderParameter,
  [ModelType.parametertemplate]: RenderParameterTemplate,
  [ModelType.manufacturerpart]: RenderManufacturerPart,
  [ModelType.notetemplate]: RenderNoteTemplate,
  [ModelType.owner]: RenderOwner,
  [ModelType.part]: RenderPart,
  [ModelType.partcategory]: RenderPartCategory,
  [ModelType.parttesttemplate]: RenderPartTestTemplate,
  [ModelType.projectcode]: RenderProjectCode,
  [ModelType.purchaseorder]: RenderPurchaseOrder,
  [ModelType.purchaseorderlineitem]: RenderPurchaseOrder,
  [ModelType.returnorder]: RenderReturnOrder,
  [ModelType.returnorderlineitem]: RenderReturnOrderLineItem,
  [ModelType.salesorder]: RenderSalesOrder,
  [ModelType.salesordershipment]: RenderSalesOrderShipment,
  [ModelType.transferorder]: RenderTransferOrder,
  [ModelType.transferorderlineitem]: RenderTransferOrderLineItem,
  [ModelType.stocklocation]: RenderStockLocation,
  [ModelType.stocklocationtype]: RenderStockLocationType,
  [ModelType.stockitem]: RenderStockItem,
  [ModelType.stockhistory]: RenderStockItem,
  [ModelType.supplierpart]: RenderSupplierPart,
  [ModelType.user]: RenderUser,
  [ModelType.group]: RenderGroup,
  [ModelType.importsession]: RenderImportSession,
  [ModelType.reporttemplate]: RenderReportTemplate,
  [ModelType.labeltemplate]: RenderLabelTemplate,
  [ModelType.pluginconfig]: RenderPlugin,
  [ModelType.contenttype]: RenderContentType,
  [ModelType.selectionlist]: RenderSelectionList,
  [ModelType.selectionentry]: RenderSelectionEntry,
  [ModelType.error]: RenderError,
  [ModelType.tag]: RenderTag
});
