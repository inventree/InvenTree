import { t } from '@lingui/core/macro';
import { Drawer, Stack, Text } from '@mantine/core';

import { StylishText } from '@lib/components/StylishText';
import type { ModelType } from '@lib/index';
import { getModelInfo } from '../render/ModelType';

export default function PreviewDrawer({
  modelType,
  instance,
  opened,
  onClose
}: Readonly<{
  modelType?: ModelType;
  instance?: any;
  opened: boolean;
  onClose: () => void;
}>) {
  const modelInfo = getModelInfo(instance.model);

  return (
    <Drawer
      position='right'
      size='lg'
      title={
        <StylishText size='lg'>
          TODO - implement actual preview content
        </StylishText>
      }
      opened={opened}
      onClose={onClose}
      withCloseButton
    >
      <Stack gap='xs'>
        <Text c='dimmed'>{t`Preview for ${modelInfo.label} #${instance.pk}`}</Text>
      </Stack>
    </Drawer>
  );
}
