import type { ModelType } from '@lib/enums/ModelType';
import { t } from '@lingui/core/macro';
import { Skeleton } from '@mantine/core';
import { IconListDetails } from '@tabler/icons-react';
import { ParameterTable } from '../../tables/general/ParameterTable';
import type { PanelType } from './Panel';

export default function ParametersPanel({
  model_type,
  model_id,
  hidden,
  allowEdit = true
}: {
  model_type: ModelType;
  model_id: number | undefined;
  hidden?: boolean;
  allowEdit?: boolean;
}): PanelType {
  return {
    name: 'parameters',
    label: t`Parameters`,
    icon: <IconListDetails />,
    hidden: hidden ?? false,
    content:
      model_type && model_id ? (
        <ParameterTable
          allowEdit={allowEdit}
          modelType={model_type}
          modelId={model_id}
        />
      ) : (
        <Skeleton />
      )
  };
}
