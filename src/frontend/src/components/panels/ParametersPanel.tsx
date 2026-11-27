import type { ModelType } from '@lib/enums/ModelType';
import type { PanelType } from '@lib/types/Panel';
import { t } from '@lingui/core/macro';
import { Skeleton, Stack } from '@mantine/core';
import { IconListDetails } from '@tabler/icons-react';
import { ParameterTable } from '../../tables/general/ParameterTable';
import { LockedItemMessage } from '../items/LockedItemMessage';

export default function ParametersPanel({
  model_type,
  model_id,
  hidden,
  allowEdit = true,
  locked = false,
  parameter_count
}: {
  model_type: ModelType;
  model_id: number | undefined;
  hidden?: boolean;
  allowEdit?: boolean;
  locked?: boolean;
  parameter_count?: number;
}): PanelType {
  return {
    name: 'parameters',
    label: t`Parameters`,
    icon: <IconListDetails />,
    hotkey: 'mod+Shift+P',
    hidden: hidden ?? false,
    notification_dot: parameter_count ? 'info' : null,
    content:
      model_type && model_id ? (
        <Stack gap='xs'>
          {locked && <LockedItemMessage />}
          <ParameterTable
            allowEdit={allowEdit && !locked}
            modelType={model_type}
            modelId={model_id}
          />
        </Stack>
      ) : (
        <Skeleton />
      )
  };
}
