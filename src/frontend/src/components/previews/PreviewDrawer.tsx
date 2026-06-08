import { t } from '@lingui/core/macro';
import { Drawer, Loader, Stack, Text } from '@mantine/core';

import { StylishText } from '@lib/components/StylishText';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/index';
import { useInstance } from '../../hooks/UseInstance';
import { getModelInfo } from '../render/ModelType';

export default function PreviewDrawer({
  modelType,
  id,
  instance: providedInstance,
  opened,
  onClose
}: Readonly<{
  modelType: ModelType;
  id: number;
  instance?: any;
  opened: boolean;
  onClose: () => void;
}>) {
  const modelInfo = getModelInfo(modelType);
  const apiEndpoint = ModelInformationDict[modelType].api_endpoint;

  const { instance: fetchedInstance, instanceQuery } = useInstance({
    endpoint: apiEndpoint,
    pk: id,
    hasPrimaryKey: true,
    defaultValue: {},
    disabled: !!providedInstance
  });

  const instance = providedInstance ?? fetchedInstance;

  return (
    <Drawer
      position='right'
      size='xl'
      title={<StylishText size='lg'>{`${modelInfo.label} #${id}`}</StylishText>}
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
        {!instance && instanceQuery.isFetching ? (
          <Loader />
        ) : (
          <Text c='dimmed'>{t`Preview for ${modelInfo.label} #${id}`}</Text>
        )}
      </Stack>
    </Drawer>
  );
}
