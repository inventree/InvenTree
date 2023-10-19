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
  return (
    <RenderInlineModel
      primary={instance.part_detail?.full_name}
      secondary={instance.quantity}
      image={instance.part_detail?.thumbnail || instance.part_detail?.image}
    />
  );
}
