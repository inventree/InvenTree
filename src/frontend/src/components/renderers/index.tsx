import { BuildOrderRenderer } from './BuildOrderRenderer';
import { PartRenderer } from './PartRenderer';
import { PurchaseOrderRenderer } from './PurchaseOrderRenderer';
import { SalesOrderRenderer } from './SalesOrderRenderer';
import { StockItemRenderer } from './StockItemRenderer';
import { StockLocationRenderer } from './StockLocationRenderer';
import { SupplierPartRenderer } from './SupplierPartRenderer';

export enum RenderTypes {
  part = 'part',
  stock_item = 'stockitem',
  stock_location = 'stocklocation',
  supplier_part = 'supplierpart',
  purchase_order = 'purchase_order',
  sales_order = 'sales_order',
  build_order = 'build_order'
}

// dict of renderers
const renderers = {
  [RenderTypes.part]: PartRenderer,
  [RenderTypes.stock_item]: StockItemRenderer,
  [RenderTypes.stock_location]: StockLocationRenderer,
  [RenderTypes.supplier_part]: SupplierPartRenderer,
  [RenderTypes.purchase_order]: PurchaseOrderRenderer,
  [RenderTypes.sales_order]: SalesOrderRenderer,
  [RenderTypes.build_order]: BuildOrderRenderer
};

export interface RenderProps {
  type: RenderTypes;
  pk: string;
}

export function Render(props: RenderProps) {
  const { type, ...rest } = props;
  const RendererComponent = renderers[type];
  return <RendererComponent {...rest} />;
}
