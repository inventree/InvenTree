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
