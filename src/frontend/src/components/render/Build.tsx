import { ReactNode } from 'react';

import { ModelType } from '../../enums/ModelType';
import { InstanceRenderInterface, RenderInlineModel } from './Instance';
import { StatusRenderer } from './StatusRenderer';

/**
 * Inline rendering of a single BuildOrder instance
 */
export function RenderBuildOrder({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
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

/*
 * Inline rendering of a single BuildLine instance
 */
export function RenderBuildLine({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.part_detail.full_name}
      secondary={instance.quantity}
      suffix={StatusRenderer({
        status: instance.status,
        type: ModelType.build
      })}
      image={instance.part_detail.thumbnail || instance.part_detail.image}
    />
  );
}
