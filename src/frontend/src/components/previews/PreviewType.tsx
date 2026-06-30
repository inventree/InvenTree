import { ModelType } from '@lib/enums/ModelType';
import type { ReactNode } from 'react';
import { PartPreviewComponent } from './models/PartPreview';
import { PurchaseOrderPreviewComponent } from './models/PurchaseOrderPreview';
import { ReturnOrderPreviewComponent } from './models/ReturnOrderPreview';
import { SalesOrderPreviewComponent } from './models/SalesOrderPreview';
import { StockPreviewComponent } from './models/StockPreview';

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
    default:
      return null;
  }
}
