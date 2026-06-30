import type { ModelType } from '@lib/enums/ModelType';
import type { ReactNode } from 'react';

export interface PreviewType {
  preview: ReactNode;
  title: string;
}

export type PreviewComponentProps = {
  instance: any;
};

export type PreviewComponent = (props: PreviewComponentProps) => PreviewType;

export function getPreviewComponentForModel({
  modelType
}: {
  modelType: ModelType;
}): PreviewType | null {
  switch (modelType) {
    default:
      // Return null to indicate that this model type is not supported
      return null;
  }
}
