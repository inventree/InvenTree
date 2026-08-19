import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { PanelType } from '@lib/types/Panel';
import { t } from '@lingui/core/macro';
import { Skeleton } from '@mantine/core';
import { IconListDetails } from '@tabler/icons-react';
import { api } from '../../App';
import { ParameterTable } from '../../tables/general/ParameterTable';

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
    hotkey: 'mod+Shift+P',
    hidden: hidden ?? false,
    notification_dot: async () => {
      if (!model_type || !model_id) {
        return null;
      }

      return api
        .get(apiUrl(ApiEndpoints.parameter_list), {
          params: {
            model_type: model_type,
            model_id: model_id,
            limit: 1
          }
        })
        .then((response) => ((response.data?.count ?? 0) > 0 ? 'info' : null));
    },
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
