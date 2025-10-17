import { ModelType } from '@lib/enums/ModelType';
import { getDetailUrl } from '@lib/functions/Navigation';
import type { ReactNode } from 'react';
import { type InstanceRenderInterface, RenderInlineModel } from './Instance';

/**
 * Inline rendering of a single Company instance
 */
export function RenderTenant(
  props: Readonly<InstanceRenderInterface>
): ReactNode {
  const { instance } = props;

  return (
    <RenderInlineModel
      {...props}
      primary={instance.name}
      suffix={instance.description}
      url={props.link ? getDetailUrl(ModelType.tenant, instance.pk) : undefined}
    />
  );
}
