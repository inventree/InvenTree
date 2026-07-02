import { ModelType } from '@lib/enums/ModelType';
import type { ReactNode } from 'react';
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

export interface PreviewType {
  preview: ReactNode;
  title: string;
}

export type PreviewComponentProps = {
  instance: any;
};

export type PreviewComponent = (props: PreviewComponentProps) => PreviewType;

export function getPreviewComponentForModel({
  modelType,
  instance,
  modelId
}: {
  modelType: ModelType;
  instance: any;
  modelId: number;
}): PreviewType | null {
  switch (modelType) {
    case ModelType.part:
      return PartPreviewComponent({ instance, modelId });
    case ModelType.stockitem:
      return StockPreviewComponent({ instance, modelId });
    case ModelType.purchaseorder:
      return PurchaseOrderPreviewComponent({ instance, modelId });
    case ModelType.salesorder:
      return SalesOrderPreviewComponent({ instance, modelId });
    case ModelType.returnorder:
      return ReturnOrderPreviewComponent({ instance, modelId });
    case ModelType.supplierpart:
      return SupplierPartPreviewComponent({ instance, modelId });
    case ModelType.manufacturerpart:
      return ManufacturerPartPreviewComponent({ instance, modelId });
    case ModelType.company:
      return CompanyPreviewComponent({ instance, modelId });
    case ModelType.build:
      return BuildOrderPreviewComponent({ instance, modelId });
    case ModelType.salesordershipment:
      return SalesOrderShipmentPreviewComponent({ instance, modelId });
    case ModelType.transferorder:
      return TransferOrderPreviewComponent({ instance, modelId });
    case ModelType.stocklocation:
      return StockLocationPreviewComponent({ instance, modelId });
    case ModelType.partcategory:
      return PartCategoryPreviewComponent({ instance, modelId });
    default:
      return null;
  }
}
