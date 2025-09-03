import { t } from '@lingui/core/macro';
import { Badge } from '@mantine/core';
import type { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

export function RenderPlugin({
  instance
}: Readonly<{
  instance: Readonly<any>;
}>): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.name}
      suffix={instance.meta?.description}
      secondary={
        !instance.active && <Badge size='sm' color='red'>{t`Inactive`}</Badge>
      }
    />
  );
}
