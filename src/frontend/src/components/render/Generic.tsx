import type { ReactNode } from 'react';

import { type InstanceRenderInterface, RenderInlineModel } from './Instance';

export function RenderParameterTemplate({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.name}
      secondary={instance.description}
      suffix={instance.units}
    />
  );
}

export function RenderParameter({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.template?.name || ''}
      secondary={instance.description}
      suffix={instance.data || instance.data_numeric || ''}
    />
  );
}

export function RenderProjectCode({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return (
    instance && (
      <RenderInlineModel
        primary={instance.code}
        suffix={instance.description}
      />
    )
  );
}

export function RenderContentType({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return instance && <RenderInlineModel primary={instance.app_labeled_name} />;
}

export function RenderError({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return instance && <RenderInlineModel primary={instance.name} />;
}

export function RenderImportSession({
  instance
}: {
  instance: any;
}): ReactNode {
  return instance && <RenderInlineModel primary={instance.data_file} />;
}

export function RenderSelectionList({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return (
    instance && (
      <RenderInlineModel
        primary={instance.name}
        secondary={instance.description}
      />
    )
  );
}
