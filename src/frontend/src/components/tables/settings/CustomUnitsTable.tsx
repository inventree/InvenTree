import { t } from '@lingui/macro';
import { ActionIcon, Text, Tooltip } from '@mantine/core';
import { IconCirclePlus } from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';

import {
  openCreateApiForm,
  openDeleteApiForm,
  openEditApiForm
} from '../../../functions/forms';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction } from '../RowActions';

/**
 * Table for displaying list of custom physical units
 */
export function CustomUnitsTable() {
  const { tableKey, refreshTable } = useTableRefresh('custom-units');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Name`,
        switchable: false,
        sortable: true
      },
      {
        accessor: 'definition',
        title: t`Definition`,
        switchable: false,
        sortable: false
      },
      {
        accessor: 'symbol',
        title: t`Symbol`,
        switchable: false,
        sortable: true
      }
    ];
  }, []);

  const rowActions = useCallback((record: any): RowAction[] => {
    return [
      {
        title: t`Edit`,
        onClick: () => {
          openEditApiForm({
            name: 'edit-custom-unit',
            url: ApiPaths.custom_unit_list,
            pk: record.pk,
            title: t`Edit custom unit`,
            fields: {
              name: {},
              definition: {},
              symbol: {}
            },
            onFormSuccess: refreshTable,
            successMessage: t`Custom unit updated`
          });
        }
      },
      {
        title: t`Delete`,
        onClick: () => {
          openDeleteApiForm({
            name: 'delete-custom-unit',
            url: ApiPaths.custom_unit_list,
            pk: record.pk,
            title: t`Delete custom unit`,
            successMessage: t`Custom unit deleted`,
            onFormSuccess: refreshTable,
            preFormContent: (
              <Text>{t`Are you sure you want to remove this custom unit?`}</Text>
            )
          });
        }
      }
    ];
  }, []);

  const addCustomUnit = useCallback(() => {
    openCreateApiForm({
      name: 'add-custom-unit',
      url: ApiPaths.custom_unit_list,
      title: t`Add custom unit`,
      fields: {
        name: {},
        definition: {},
        symbol: {}
      },
      successMessage: t`Custom unit created`,
      onFormSuccess: refreshTable
    });
  }, []);

  const tableActions = useMemo(() => {
    let actions = [];

    actions.push(
      <Tooltip label={t`Add custom unit`}>
        <ActionIcon radius="sm" onClick={addCustomUnit}>
          <IconCirclePlus color="green" />
        </ActionIcon>
      </Tooltip>
    );

    return actions;
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.custom_unit_list)}
      tableKey={tableKey}
      columns={columns}
      props={{
        rowActions: rowActions,
        customActionGroups: tableActions
      }}
    />
  );
}
