import { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

/**
 * Inline rendering of a single StockLocation instance
 */
export function RenderStockLocation({
  location
}: {
  location: any;
}): ReactNode {
  return (
    <RenderInlineModel
      primary={location.name}
      secondary={location.description}
    />
  );
}

export function RenderStockItem({ item }: { item: any }): ReactNode {
  return (
    <RenderInlineModel
      primary={item.part_detail?.full_name}
      secondary={item.quantity}
      image={item.part_detail?.thumbnail || item.part_detail?.image}
    />
  );
}
