import { t } from '@lingui/macro';
import type { ReactNode } from 'react';

import { ModelType } from '../../enums/ModelType';
import { getDetailUrl } from '../../functions/urls';
import { type InstanceRenderInterface, RenderInlineModel } from './Instance';
import { StatusRenderer } from './StatusRenderer';

/**
 * Inline rendering of a single PurchaseOrder instance
 */
export function RenderPurchaseOrder(
  props: Readonly<InstanceRenderInterface>
): ReactNode {
  const { instance } = props;
  const supplier = instance?.supplier_detail || {};

  return (
    <RenderInlineModel
      {...props}
      primary={instance.reference}
      secondary={instance.description}
      suffix={StatusRenderer({
        status: instance.status_custom_key,
        type: ModelType.purchaseorder
      })}
      image={supplier.thumnbnail || supplier.image}
      url={
        props.link
          ? getDetailUrl(ModelType.purchaseorder, instance.pk)
          : undefined
      }
    />
  );
}

/**
 * Inline rendering of a single ReturnOrder instance
 */
export function RenderReturnOrder(
  props: Readonly<InstanceRenderInterface>
): ReactNode {
  const { instance } = props;
  const customer = instance?.customer_detail || {};

  return (
    <RenderInlineModel
      {...props}
      primary={instance.reference}
      secondary={instance.description}
      suffix={StatusRenderer({
        status: instance.status_custom_key,
        type: ModelType.returnorder
      })}
      image={customer.thumnbnail || customer.image}
      url={
        props.link
          ? getDetailUrl(ModelType.returnorder, instance.pk)
          : undefined
      }
    />
  );
}

export function RenderReturnOrderLineItem(
  props: Readonly<InstanceRenderInterface>
): ReactNode {
  const { instance } = props;

  return (
    <RenderInlineModel
      {...props}
      primary={instance.reference}
      suffix={StatusRenderer({
        status: instance.outcome,
        type: ModelType.returnorderlineitem
      })}
    />
  );
}

/**
 * Inline rendering of a single SalesOrder instance
 */
export function RenderSalesOrder(
  props: Readonly<InstanceRenderInterface>
): ReactNode {
  const { instance } = props;
  const customer = instance?.customer_detail || {};

  return (
    <RenderInlineModel
      {...props}
      primary={instance.reference}
      secondary={instance.description}
      suffix={StatusRenderer({
        status: instance.status_custom_key,
        type: ModelType.salesorder
      })}
      image={customer.thumnbnail || customer.image}
      url={
        props.link ? getDetailUrl(ModelType.salesorder, instance.pk) : undefined
      }
    />
  );
}

/**
 * Inline rendering of a single SalesOrderAllocation instance
 */
export function RenderSalesOrderShipment({
  instance
}: Readonly<{
  instance: any;
}>): ReactNode {
  const order = instance.order_detail || {};

  return (
    <RenderInlineModel
      primary={order.reference}
      secondary={`${t`Shipment`} ${instance.reference}`}
    />
  );
}
