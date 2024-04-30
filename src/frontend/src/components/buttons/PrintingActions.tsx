import { t } from '@lingui/macro';
import { ActionIcon, Menu, Tooltip } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconPrinter, IconReport, IconTags } from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';

import { api } from '../../App';
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

  const printLabels = useCallback(() => {
    // Fetch available label templates
    api.get(apiUrl(ApiEndpoints.label_list), {
      params: {
        enabled: true,
        model_type: modelType,
        items: items.join(',')
      }
    });
  }, [items]);

  const printReports = useCallback(() => {
    reportModal.open();
  }, [items]);

  if (!modelType) {
    return null;
  }

  if (!enableLabels && !enableReports) {
    return null;
  }

  const reportModal = useCreateApiFormModal({
    fetchInitialData: false,
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
              onClick={printLabels}
            >{t`Print Labels`}</Menu.Item>
          )}
          {enableReports && (
            <Menu.Item
              key="reports"
              icon={<IconReport />}
              onClick={printReports}
            >{t`Print Reports`}</Menu.Item>
          )}
        </Menu.Dropdown>
      </Menu>
    </>
  );
}
