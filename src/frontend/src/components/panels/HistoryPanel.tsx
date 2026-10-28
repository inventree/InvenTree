import { t } from '@lingui/core/macro';
import { Skeleton } from '@mantine/core';
import { IconHistory } from '@tabler/icons-react';

import type { ModelType } from '@lib/enums/ModelType';
import type { PanelType } from '@lib/types/Panel';
import { AuditLogTable } from '../../tables/general/AuditLogTable';

/**
 * Panel displaying the audit log (change history) for a model instance.
 */
export default function HistoryPanel({
  model_type,
  model_id,
  visible
}: {
  model_type: ModelType;
  model_id: number | undefined;
  visible: boolean;
}): PanelType {
  return {
    name: 'history',
    label: t`History`,
    icon: <IconHistory />,
    hidden: !visible,
    content:
      visible && model_type && model_id ? (
        <AuditLogTable modelType={model_type} modelId={model_id} />
      ) : (
        <Skeleton />
      )
  };
}
