import type { ModelInformationInterface } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
import { t } from '@lingui/core/macro';
import { Alert, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import type { PreviewType } from '../PreviewType';

export function FallbackPreviewComponent({
  modelInfo,
  modelType,
  modelId,
  instance
}: {
  modelInfo: ModelInformationInterface;
  modelType: ModelType;
  modelId: number | string;
  instance: any;
}): PreviewType {
  return {
    title: `${modelInfo.label} #${modelId}`,
    preview: (
      <Alert
        color='red'
        title={t`No preview available`}
        icon={<IconExclamationCircle />}
      >
        <Text>{t`No preview available for this model.`}</Text>
      </Alert>
    )
  };
}
