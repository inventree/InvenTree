import { ModelType } from '@lib/enums/ModelType';
import type { ReactNode } from 'react';
import { PartPreviewComponent } from './models/PartPreview';

export interface PreviewType {
  preview: ReactNode;
  title: string;
}

export type PreviewComponentProps = {
  instance: any;
};

export type PreviewComponent = (props: PreviewComponentProps) => PreviewType;

export function getPreviewComponentForModel({
  modelType,
  instance,
  modelId
}: {
  modelType: ModelType;
  instance: any;
  modelId: number;
}): PreviewType | null {
  switch (modelType) {
    case ModelType.part:
      return PartPreviewComponent({ instance, modelId });
    default:
      return null;
  }
}
