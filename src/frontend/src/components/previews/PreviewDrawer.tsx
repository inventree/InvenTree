import { Divider, Drawer, LoadingOverlay, Stack } from '@mantine/core';

import { StylishText } from '@lib/components/StylishText';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/index';
import { useMemo } from 'react';
import { useInstance } from '../../hooks/UseInstance';
import { getModelInfo } from '../render/ModelType';
import { type PreviewType, getPreviewComponentForModel } from './PreviewType';
import { FallbackPreviewComponent } from './models/Fallback';

export default function PreviewDrawer({
  modelType,
  id,
  instance: providedInstance,
  filters,
  opened,
  onClose
}: Readonly<{
  modelType?: ModelType;
  id?: number | string;
  instance?: any;
  filters?: Record<string, any>;
  opened: boolean;
  onClose: () => void;
}>) {
  const modelInfo = modelType ? getModelInfo(modelType) : null;
  const apiEndpoint = modelType
    ? ModelInformationDict[modelType].api_endpoint
    : undefined;

  const { instance: fetchedInstance, instanceQuery } = useInstance({
    endpoint: apiEndpoint!,
    pk: id,
    hasPrimaryKey: true,
    defaultValue: {},
    params: filters,
    disabled: !!providedInstance || !modelType || !id
  });

  const instance = useMemo(() => {
    return providedInstance ?? fetchedInstance;
  }, [providedInstance, fetchedInstance]);

  const previewComponent: PreviewType | null = useMemo(() => {
    if (!modelType || !modelInfo || id == null) return null;

    const component: PreviewType | null = getPreviewComponentForModel({
      modelType,
      instance,
      modelId: typeof id === 'string' ? Number(id) : id
    });

    if (component == null) {
      return FallbackPreviewComponent({
        modelInfo,
        modelType,
        modelId: id,
        instance
      });
    }

    return component;
  }, [modelType, id, instance]);

  return (
    <Drawer
      position='right'
      size='xl'
      title={
        previewComponent ? (
          <StylishText size='lg'>{previewComponent.title}</StylishText>
        ) : null
      }
      opened={opened}
      onClose={onClose}
      withCloseButton
      transitionProps={{
        transition: 'slide-left',
        duration: 300,
        timingFunction: 'ease'
      }}
    >
      <Stack gap='xs'>
        {previewComponent && (
          <>
            <Divider />
            <LoadingOverlay visible={instanceQuery.isFetching} />
            {previewComponent.preview}
          </>
        )}
      </Stack>
    </Drawer>
  );
}
