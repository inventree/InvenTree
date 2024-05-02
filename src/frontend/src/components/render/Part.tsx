import { t } from '@lingui/macro';
import { ReactNode } from 'react';

import { InstanceRenderInterface, RenderInlineModel } from './Instance';

/**
 * Inline rendering of a single Part instance
 */
export function RenderPart({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  const stock = t`Stock` + `: ${instance.in_stock}`;

  return (
    <RenderInlineModel
      primary={instance.name}
      secondary={instance.description}
      suffix={stock}
      image={instance.thumnbnail || instance.image}
    />
  );
}

/**
 * Inline rendering of a PartCategory instance
 */
export function RenderPartCategory({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  // TODO: Handle URL

  let lvl = '-'.repeat(instance.level || 0);

  return (
    <RenderInlineModel
      primary={`${lvl} ${instance.name}`}
      secondary={instance.description}
    />
  );
}

/**
 * Inline rendering of a PartParameterTemplate instance
 */
export function RenderPartParameterTemplate({
  instance
}: {
  instance: any;
}): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.name}
      secondary={instance.description}
      suffix={instance.units}
    />
  );
}

export function RenderPartTestTemplate({
  instance
}: {
  instance: any;
}): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.test_name}
      secondary={instance.description}
    />
  );
}
