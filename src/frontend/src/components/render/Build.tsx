import { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

/**
 * Inline rendering of a single BuildOrder instance
 */
export function RenderBuildOrder({
  buildorder
}: {
  buildorder: any;
}): ReactNode {
  return (
    <RenderInlineModel
      primary={buildorder.reference}
      secondary={buildorder.title}
      image={buildorder.part_detail?.thumbnail || buildorder.part_detail?.image}
    />
  );
}
