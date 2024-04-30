import { t } from '@lingui/macro';
import { ActionIcon, Menu, Tooltip } from '@mantine/core';
import { IconPrinter, IconReport, IconTags } from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';

import { ModelType } from '../enums/ModelType';
import { TableState } from '../hooks/UseTable';

export function PrintingAction({
  tableState,
  enableLabels,
  enableReports,
  modelType
}: {
  tableState: TableState;
  enableLabels?: boolean;
  enableReports?: boolean;
  modelType?: ModelType;
}) {
  const enabled = useMemo(
    () => tableState.hasSelectedRecords,
    [tableState.hasSelectedRecords]
  );

  const printLabels = useCallback(() => {
    // TODO
  }, [tableState]);

  const printReports = useCallback(() => {
    // TODO
  }, [tableState]);

  if (!modelType) {
    return null;
  }

  if (!enableLabels && !enableReports) {
    return null;
  }

  return (
    <>
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
