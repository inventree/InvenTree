import { t } from '@lingui/macro';
import { Badge } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import type {
  StatusCodeInterface,
  StatusCodeListInterface
} from '../../components/render/StatusRenderer';
import { statusColorMap } from '../../defaults/backendMappings';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { useCustomStateFields } from '../../forms/CommonForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useGlobalStatusState } from '../../states/StatusState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import type { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import {
  type RowAction,
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction
} from '../RowActions';

/**
 * Table for displaying list of custom states
 */
export default function CustomStateTable() {
  const table = useTable('customstates');

  const statusCodes = useGlobalStatusState();

  // Find the associated logical state key
  const getLogicalState = useCallback(
    (group: string, key: number) => {
      const valuesList = Object.values(statusCodes.status ?? {}).find(
        (value: StatusCodeListInterface) => value.status_class === group
      );

      const value = Object.values(valuesList?.values ?? {}).find(
        (value: StatusCodeInterface) => value.key === key
      );

      return value?.label ?? value?.name ?? '';
    },
    [statusCodes]
  );

  const user = useUserState();

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'reference_status',
        label: t`Status Group`,
        field_type: 'choice',
        choices: Object.values(statusCodes.status ?? {}).map(
          (value: StatusCodeListInterface) => ({
            label: value.status_class,
            value: value.status_class
          })
        )
      }
    ];
  }, [statusCodes]);

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'reference_status',
        title: t`Status`,
        sortable: true
      },
      {
        accessor: 'logical_key',
        title: t`Logical State`,
        sortable: true,
        render: (record: any) => {
          const stateText = getLogicalState(
            record.reference_status,
            record.logical_key
          );
          return stateText ? stateText : record.logical_key;
        }
      },
      {
        accessor: 'name',
        title: t`Identifier`,
        sortable: true
      },
      {
        accessor: 'label',
        title: t`Display Name`,
        sortable: true
      },
      {
        accessor: 'key',
        sortable: true
      },
      {
        accessor: 'color',
        render: (record: any) => {
          return (
            <Badge
              color={statusColorMap[record.color] || statusColorMap['default']}
              variant='filled'
              size='xs'
            >
              {record.color}
            </Badge>
          );
        }
      }
    ];
  }, [getLogicalState]);

  const newCustomStateFields = useCustomStateFields();
  const duplicateCustomStateFields = useCustomStateFields();
  const editCustomStateFields = useCustomStateFields();

  const [initialStateData, setInitialStateData] = useState<any>({});

  const newCustomState = useCreateApiFormModal({
    url: ApiEndpoints.custom_state_list,
    title: t`Add State`,
    fields: newCustomStateFields,
    table: table
  });

  const duplicateCustomState = useCreateApiFormModal({
    url: ApiEndpoints.custom_state_list,
    title: t`Add State`,
    fields: duplicateCustomStateFields,
    initialData: initialStateData,
    table: table
  });

  const [selectedCustomState, setSelectedCustomState] = useState<
    number | undefined
  >(undefined);

  const editCustomState = useEditApiFormModal({
    url: ApiEndpoints.custom_state_list,
    pk: selectedCustomState,
    title: t`Edit State`,
    fields: editCustomStateFields,
    table: table
  });

  const deleteCustomState = useDeleteApiFormModal({
    url: ApiEndpoints.custom_state_list,
    pk: selectedCustomState,
    title: t`Delete State`,
    table: table
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.admin),
          onClick: () => {
            setSelectedCustomState(record.pk);
            editCustomState.open();
          }
        }),
        RowDuplicateAction({
          hidden: !user.hasAddRole(UserRoles.admin),
          onClick: () => {
            setInitialStateData(record);
            duplicateCustomState.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.admin),
          onClick: () => {
            setSelectedCustomState(record.pk);
            deleteCustomState.open();
          }
        })
      ];
    },
    [user]
  );

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key={'add'}
        onClick={() => {
          setInitialStateData({});
          newCustomState.open();
        }}
        tooltip={t`Add State`}
      />
    ];
  }, []);

  return (
    <>
      {newCustomState.modal}
      {editCustomState.modal}
      {duplicateCustomState.modal}
      {deleteCustomState.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.custom_state_list)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions,
          tableFilters: tableFilters,
          enableDownload: true
        }}
      />
    </>
  );
}
