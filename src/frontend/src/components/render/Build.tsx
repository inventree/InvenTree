import { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

/**
 * Inline rendering of a single BuildOrder instance
 */
export function RenderBuildOrder({ instance }: { instance: any }): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.reference}
      secondary={instance.title}
      image={instance.part_detail?.thumbnail || instance.part_detail?.image}
    />
  );
}
