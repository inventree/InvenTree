import type { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

export function RenderReportTemplate({
  instance
}: Readonly<{
  instance: any;
}>): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.name}
      secondary={instance.description}
    />
  );
}

export function RenderLabelTemplate({
  instance
}: Readonly<{
  instance: any;
}>): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.name}
      secondary={instance.description}
    />
  );
}
