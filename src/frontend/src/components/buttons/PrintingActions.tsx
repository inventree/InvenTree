import { t } from '@lingui/macro';
import { ActionIcon, Menu, Tooltip } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconPrinter, IconReport, IconTags } from '@tabler/icons-react';
import { useMemo } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { apiUrl } from '../../states/ApiState';
import { useLocalState } from '../../states/LocalState';

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
      console.log('response:', response);
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
        console.log('url:', response.output, '->', url);
        window.open(url, '_blank');
      }
    }
  });

  return (
    <>
      {reportModal.modal}
      {labelModal.modal}
      <Menu withinPortal disabled={!enabled}>
        <Menu.Target>
          <ActionIcon disabled={!enabled}>
            <Tooltip label={t`Printing actions`}>
              <IconPrinter />
            </Tooltip>
          </ActionIcon>
        </Menu.Target>
        <Menu.Dropdown>
          {enableLabels && (
            <Menu.Item
              key="labels"
              icon={<IconTags />}
              onClick={() => labelModal.open()}
            >{t`Print Labels`}</Menu.Item>
          )}
          {enableReports && (
            <Menu.Item
              key="reports"
              icon={<IconReport />}
              onClick={() => reportModal.open()}
            >{t`Print Reports`}</Menu.Item>
          )}
        </Menu.Dropdown>
      </Menu>
    </>
  );
}
