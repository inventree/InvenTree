import { t } from '@lingui/macro';
import { notifications } from '@mantine/notifications';
import { IconPrinter, IconReport, IconTags } from '@tabler/icons-react';
import { useMemo } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { apiUrl } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';
import { ActionDropdown } from '../items/ActionDropdown';

export function PrintingActions({
  items,
  enableLabels,
  enableReports,
  modelType
}: {
  items: number[];
  enableLabels?: boolean;
  enableReports?: boolean;
  modelType?: ModelType;
}) {
  const { host } = useLocalState.getState();

  const enabled = useMemo(() => items.length > 0, [items]);

  if (!modelType) {
    return null;
  }

  if (!enableLabels && !enableReports) {
    return null;
  }

  const labelModal = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.label_print),
    title: t`Print Label`,
    fields: {
      template: {
        filters: {
          enabled: true,
          model_type: modelType,
          items: items.join(',')
        }
      },
      plugin: {
        filters: {
          active: true,
          mixin: 'labels'
        }
      },
      items: {
        hidden: true,
        value: items
      }
    },
    onFormSuccess: (response: any) => {
      if (!response.complete) {
        // TODO: Periodically check for completion
        notifications.show({
          title: t`Error`,
          message: t`The label could not be generated`,
          color: 'red'
        });
        return;
      }

      notifications.show({
        title: t`Success`,
        message: t`Label printing completed successfully`,
        color: 'green'
      });

      if (response.output) {
        // An output file was generated
        const url = `${host}${response.output}`;
        window.open(url, '_blank');
      }
    }
  });

  const reportModal = useCreateApiFormModal({
    title: t`Print Report`,
    url: apiUrl(ApiEndpoints.report_print),
    fields: {
      template: {
        filters: {
          enabled: true,
          model_type: modelType,
          items: items.join(',')
        }
      },
      items: {
        hidden: true,
        value: items
      }
    },
    onFormSuccess: (response: any) => {
      if (!response.complete) {
        // TODO: Periodically check for completion
        notifications.show({
          title: t`Error`,
          message: t`The report could not be generated`,
          color: 'red'
        });
        return;
      }

      notifications.show({
        title: t`Success`,
        message: t`Report printing completed successfully`,
        color: 'green'
      });

      if (response.output) {
        // An output file was generated
        const url = `${host}${response.output}`;
        window.open(url, '_blank');
      }
    }
  });

  return (
    <>
      {reportModal.modal}
      {labelModal.modal}
      <ActionDropdown
        key="printing"
        icon={<IconPrinter />}
        disabled={!enabled}
        actions={[
          {
            name: t`Print Labels`,
            icon: <IconTags />,
            onClick: () => labelModal.open(),
            hidden: !enableLabels
          },
          {
            name: t`Print Reports`,
            icon: <IconReport />,
            onClick: () => reportModal.open(),
            hidden: !enableReports
          }
        ]}
      />
    </>
  );
}
