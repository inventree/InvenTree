import { t } from '@lingui/macro';
import { ActionIcon, Menu, Tooltip } from '@mantine/core';
import { IconPrinter, IconReport, IconTags } from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useApiFormModal, useCreateApiFormModal } from '../../hooks/UseForm';
import { apiUrl } from '../../states/ApiState';

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

    // // Fetch available report templates
    // api.get(apiUrl(ApiEndpoints.report_list), {
    //   params: {
    //     enabled: true,
    //     model_type: modelType,
    //     items: items.join(',')
    //   }
    // });
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
