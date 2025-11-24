import type { ModelType } from '@lib/enums/ModelType';
import { t } from '@lingui/core/macro';
import { Skeleton } from '@mantine/core';
import { IconList } from '@tabler/icons-react';
import { ParameterTable } from '../../tables/general/ParameterTable';
import type { PanelType } from './Panel';

export default function ParametersPanel({
  model_type,
  model_id
}: {
  model_type: ModelType;
  model_id: number | undefined;
}): PanelType {
  return {
    name: 'parameters',
    label: t`Parameters`,
    icon: <IconList />,
    content:
      model_type && model_id ? (
        <ParameterTable modelType={model_type} modelId={model_id} />
      ) : (
        <Skeleton />
      )
  };
}
