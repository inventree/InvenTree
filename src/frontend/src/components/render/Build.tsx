import { ReactNode } from 'react';

import { ModelType } from '../../enums/ModelType';
import { RenderInlineModel } from './Instance';
import { StatusRenderer } from './StatusRenderer';

/**
 * Inline rendering of a single BuildOrder instance
 */
export function RenderBuildOrder({ instance }: { instance: any }): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.reference}
      secondary={instance.title}
      suffix={StatusRenderer({
        status: instance.status,
        type: ModelType.build
      })}
      image={instance.part_detail?.thumbnail || instance.part_detail?.image}
    />
  );
}
