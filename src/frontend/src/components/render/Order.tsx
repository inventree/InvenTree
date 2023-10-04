import { t } from '@lingui/macro';
import { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

/**
 * Inline rendering of a single PurchaseOrder instance
 */
export function RenderPurchaseOrder({ order }: { order: any }): ReactNode {
  let supplier = order.supplier_detail || {};

  // TODO: Handle URL
  return (
    <RenderInlineModel
      primary={order.reference}
      secondary={order.description}
      image={supplier.thumnbnail || supplier.image}
    />
  );
}

/**
 * Inline rendering of a single ReturnOrder instance
 */
export function RenderReturnOrder({ order }: { order: any }): ReactNode {
  let customer = order.customer_detail || {};

  return (
    <RenderInlineModel
      primary={order.reference}
      secondary={order.description}
      image={customer.thumnbnail || customer.image}
    />
  );
}

/**
 * Inline rendering of a single SalesOrder instance
 */
export function RenderSalesOrder({ order }: { order: any }): ReactNode {
  let customer = order.customer_detail || {};

  // TODO: Handle URL

  return (
    <RenderInlineModel
      primary={order.reference}
      secondary={order.description}
      image={customer.thumnbnail || customer.image}
    />
  );
}

/**
 * Inline rendering of a single SalesOrderAllocation instance
 */
export function RenderSalesOrderShipment({
  shipment
}: {
  shipment: any;
}): ReactNode {
  let order = shipment.sales_order_detail || {};

  return (
    <RenderInlineModel
      primary={order.reference}
      secondary={t`Shipment` + ` ${shipment.description}`}
    />
  );
}
