import { t } from '@lingui/macro';
import { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

/**
 * Inline rendering of a single StockLocation instance
 */
export function RenderStockLocation({
  instance
}: {
  instance: any;
}): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.name}
      secondary={instance.description}
    />
  );
}

export function RenderStockItem({ instance }: { instance: any }): ReactNode {
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
