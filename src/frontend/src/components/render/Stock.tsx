import { t } from '@lingui/macro';
import { ReactNode } from 'react';

import { InstanceRenderInterface, RenderInlineModel } from './Instance';

/**
 * Inline rendering of a single StockLocation instance
 */
export function RenderStockLocation({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.name}
      secondary={instance.description}
    />
  );
}

/**
 * Inline rendering of a single StockLocationType instance
 */
export function RenderStockLocationType({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.name}
      // TODO: render location icon here too (ref: #7237)
      secondary={instance.description + ` (${instance.location_count})`}
    />
  );
}

export function RenderStockItem({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  let quantity_string = '';

  if (instance?.serial !== null && instance?.serial !== undefined) {
    quantity_string += t`Serial Number` + `: ${instance.serial}`;
  } else if (instance?.quantity) {
    quantity_string = t`Quantity` + `: ${instance.quantity}`;
  }

  return (
    <RenderInlineModel
      primary={instance.part_detail?.full_name}
      suffix={quantity_string}
      image={instance.part_detail?.thumbnail || instance.part_detail?.image}
    />
  );
}
