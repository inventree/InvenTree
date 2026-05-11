import type { ReactNode } from 'react';

import { RenderInlineModel } from './RenderInlineModel';

export function RenderReportTemplate({
  instance
}: Readonly<{
  instance: any;
}>): ReactNode {
  return (
    <RenderInlineModel primary={instance.name} suffix={instance.description} />
  );
}

export function RenderLabelTemplate({
  instance
}: Readonly<{
  instance: any;
}>): ReactNode {
  return (
    <RenderInlineModel primary={instance.name} suffix={instance.description} />
  );
}
