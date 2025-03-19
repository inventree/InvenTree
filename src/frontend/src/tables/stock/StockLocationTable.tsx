import { t } from '@lingui/macro';
import { Group } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/buttons/AddItemButton';
import { ApiEndpoints } from '@lib/core';
import { ModelType } from '@lib/core';
import { UserRoles } from '@lib/core';
import { apiUrl } from '@lib/functions';
import { useTable } from '@lib/hooks';
import type { RowAction, TableColumn } from '@lib/tables';
import { ActionDropdown } from '../../components/items/ActionDropdown';
import { ApiIcon } from '../../components/items/ApiIcon';
import { stockLocationFields } from '../../forms/StockForms';
import {
  useBulkEditApiFormModal,
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';
import { BooleanColumn, DescriptionColumn } from '../ColumnRenderers';

import { InvenTreeIcon } from '@lib/components';
import type { TableFilter } from '@lib/tables';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowEditAction } from '../RowActions';

/**
 * Stock location table
 */
export function StockLocationTable({ parentId }: Readonly<{ parentId?: any }>) {
  const table = useTable('stocklocation');
  const user = useUserState();

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'cascade',
        label: t`Include Sublocations`,
        description: t`Include sublocations in results`
      },
      {
        name: 'structural',
        label: t`Structural`,
        description: t`Show structural locations`
      },
      {
        name: 'external',
        label: t`External`,
        description: t`Show external locations`
      },
      {
        name: 'has_location_type',
        label: t`Has location type`
      },
      {
        name: 'location_type',
        label: t`Location Type`,
        description: t`Filter by location type`,
        apiUrl: apiUrl(ApiEndpoints.stock_location_type_list),
        model: ModelType.stocklocationtype,
        modelRenderer: (instance: any) => instance.name
      }
    ];
  }, []);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        switchable: false,
        render: (record: any) => (
          <Group gap='xs'>
            {record.icon && <ApiIcon name={record.icon} />}
            {record.name}
          </Group>
        )
      },
      DescriptionColumn({}),
      {
        accessor: 'pathstring',
        sortable: true
      },
      {
        accessor: 'items',
        sortable: true
      },
      BooleanColumn({
        accessor: 'structural'
      }),
      BooleanColumn({
        accessor: 'external'
      }),
      {
        accessor: 'location_type',
        sortable: false,
        render: (record: any) => record.location_type_detail?.name
      }
    ];
  }, []);

  const newLocation = useCreateApiFormModal({
    url: ApiEndpoints.stock_location_list,
    title: t`Add Stock Location`,
    fields: stockLocationFields(),
    focus: 'name',
    initialData: {
      parent: parentId
    },
    follow: true,
    modelType: ModelType.stocklocation,
    table: table
  });

  const [selectedLocation, setSelectedLocation] = useState<number>(-1);

  const editLocation = useEditApiFormModal({
    url: ApiEndpoints.stock_location_list,
    pk: selectedLocation,
    title: t`Edit Stock Location`,
    fields: stockLocationFields(),
    onFormSuccess: (record: any) => table.updateRecord(record)
  });

  const setParent = useBulkEditApiFormModal({
    url: ApiEndpoints.stock_location_list,
    items: table.selectedIds,
    title: t`Set Parent Location`,
    fields: {
      parent: {}
    },
    onFormSuccess: table.refreshTable
  });

  const tableActions = useMemo(() => {
    const can_add = user.hasAddRole(UserRoles.stock_location);
    const can_edit = user.hasChangeRole(UserRoles.stock_location);

    return [
      <ActionDropdown
        tooltip={t`Location Actions`}
        icon={<InvenTreeIcon icon='location' />}
        disabled={!table.hasSelectedRecords}
        actions={[
          {
            name: t`Set Parent`,
            icon: <InvenTreeIcon icon='location' />,
            tooltip: t`Set parent location for the selected items`,
            hidden: !can_edit,
            disabled: !table.hasSelectedRecords,
            onClick: () => {
              setParent.open();
            }
          }
        ]}
      />,
      <AddItemButton
        key='add-stock-location'
        tooltip={t`Add Stock Location`}
        onClick={() => newLocation.open()}
        hidden={!can_add}
      />
    ];
  }, [user, table.hasSelectedRecords]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const can_edit = user.hasChangeRole(UserRoles.stock_location);

      return [
        RowEditAction({
          hidden: !can_edit,
          onClick: () => {
            setSelectedLocation(record.pk);
            editLocation.open();
          }
        })
      ];
    },
    [user]
  );

  return (
    <>
      {newLocation.modal}
      {editLocation.modal}
      {setParent.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.stock_location_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableSelection: true,
          enableDownload: true,
          enableLabels: true,
          enableReports: true,
          params: {
            parent: parentId,
            top_level: parentId === undefined ? true : undefined
          },
          tableFilters: tableFilters,
          tableActions: tableActions,
          rowActions: rowActions,
          modelType: ModelType.stocklocation
        }}
      />
    </>
  );
}
