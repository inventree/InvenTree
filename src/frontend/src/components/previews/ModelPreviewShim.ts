import { registerModelPreviews } from '@lib/enums/ModelInformation';
import { BuildOrderPreviewComponent } from './models/BuildOrderPreview';
import { CompanyPreviewComponent } from './models/CompanyPreview';
import { ManufacturerPartPreviewComponent } from './models/ManufacturerPartPreview';
import { PartCategoryPreviewComponent } from './models/PartCategoryPreview';
import { PartPreviewComponent } from './models/PartPreview';
import { PurchaseOrderPreviewComponent } from './models/PurchaseOrderPreview';
import { ReturnOrderPreviewComponent } from './models/ReturnOrderPreview';
import { SalesOrderPreviewComponent } from './models/SalesOrderPreview';
import { SalesOrderShipmentPreviewComponent } from './models/SalesOrderShipmentPreview';
import { StockLocationPreviewComponent } from './models/StockLocationPreview';
import { StockPreviewComponent } from './models/StockPreview';
import { SupplierPartPreviewComponent } from './models/SupplierPartPreview';
import { TransferOrderPreviewComponent } from './models/TransferOrderPreview';

registerModelPreviews({
  part: PartPreviewComponent,
  supplierpart: SupplierPartPreviewComponent,
  manufacturerpart: ManufacturerPartPreviewComponent,
  partcategory: PartCategoryPreviewComponent,
  stockitem: StockPreviewComponent,
  stocklocation: StockLocationPreviewComponent,
  build: BuildOrderPreviewComponent,
  company: CompanyPreviewComponent,
  purchaseorder: PurchaseOrderPreviewComponent,
  salesorder: SalesOrderPreviewComponent,
  salesordershipment: SalesOrderShipmentPreviewComponent,
  returnorder: ReturnOrderPreviewComponent,
  transferorder: TransferOrderPreviewComponent
});
