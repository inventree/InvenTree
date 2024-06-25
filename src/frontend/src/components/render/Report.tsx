import { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

export function RenderReportTemplate({
  instance
}: {
  instance: any;
}): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.name}
      secondary={instance.description}
    />
  );
}

export function RenderLabelTemplate({
  instance
}: {
  instance: any;
}): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.name}
      secondary={instance.description}
    />
  );
}
