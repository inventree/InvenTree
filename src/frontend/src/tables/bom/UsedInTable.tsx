import { t } from '@lingui/core/macro';
import { Alert, Divider, Group, Stack, Text } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import { ActionButton, RowEditAction, UserRoles } from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { RowAction, TableColumn } from '@lib/types/Tables';
import { IconExclamationCircle, IconReplace } from '@tabler/icons-react';
import { formatDecimal } from '../../defaults/formatters';
import { bomItemFields } from '../../forms/BomForms';
import {
  useBulkEditApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';
import {
  DescriptionColumn,
  IPNColumn,
  PartColumn,
  ReferenceColumn,
  RenderPartColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

/*
 * For a given part, render a table showing all the assemblies the part is used in
 */
export function UsedInTable({
  partId,
  params = {}
}: Readonly<{
  partId: number;
  params?: any;
}>) {
  const table = useTable('usedin');

  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({
        title: t`Assembly`,
        part: 'part_detail'
      }),
      IPNColumn({
        sortable: true
      }),
      {
        accessor: 'part_detail.revision',
        title: t`Revision`,
        sortable: true,
        defaultVisible: false
      },
      DescriptionColumn({
        accessor: 'part_detail.description'
      }),
      PartColumn({
        accessor: 'sub_part',
        sortable: true,
        title: t`Component`,
        part: 'sub_part_detail'
      }),
      {
        accessor: 'quantity',
        switchable: false,
        render: (record: any) => {
          const quantity = formatDecimal(record.quantity);
          const units = record.sub_part_detail?.units;

          return (
            <Group justify='space-between' grow wrap='nowrap'>
              <Text>{quantity}</Text>
              {units && <Text size='xs'>{units}</Text>}
            </Group>
          );
        }
      },
      ReferenceColumn({})
    ];
  }, [partId]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'inherited',
        label: t`Inherited`,
        description: t`Show inherited items`
      },
      {
        name: 'part_locked',
        label: t`Locked`,
        description: t`Show locked assemblies`
      },
      {
        name: 'optional',
        label: t`Optional`,
        description: t`Show optional items`
      },
      {
        name: 'part_active',
        label: t`Active`,
        description: t`Show active assemblies`
      },
      {
        name: 'part_trackable',
        label: t`Trackable`,
        description: t`Show trackable assemblies`
      }
    ];
  }, [partId]);

  const [selectedBomItem, setSelectedBomItem] = useState<any>({});

  const editBomItem = useEditApiFormModal({
    url: ApiEndpoints.bom_list,
    pk: selectedBomItem.pk,
    title: t`Edit BOM Item`,
    fields: bomItemFields({
      showAssembly: true
    }),
    successMessage: t`BOM item updated`,
    table: table
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const locked = record.part_detail?.locked;

      return [
        RowEditAction({
          hidden:
            locked ||
            record.sub_part != partId ||
            !user.hasChangeRole(UserRoles.bom),
          onClick: () => {
            setSelectedBomItem(record);
            editBomItem.open();
          }
        })
      ];
    },
    [user, partId]
  );

  const bulkReplaceRecords: any[] = useMemo(() => {
    // Only allow replacements of BomItem entries which point to this part
    return table.selectedRecords.filter(
      (record: any) => record.sub_part === partId
    );
  }, [table.selectedRecords, partId]);

  const bulkReplace = useBulkEditApiFormModal({
    url: ApiEndpoints.bom_list,
    items: bulkReplaceRecords.map((record: any) => record.pk),
    title: t`Replace Component`,
    submitText: t`Replace`,
    preFormContent: (
      <Stack gap='xs'>
        <Alert
          color='orange'
          icon={<IconReplace />}
          title={t`Replace Component`}
          mb='md'
        >
          <Text>{t`This action cannot be easily undone, so please ensure you have selected the correct assemblies.`}</Text>
        </Alert>
        {bulkReplaceRecords.length ? (
          <Text>{t`The selected assemblies will be updated with the new component.`}</Text>
        ) : (
          <Alert
            color='red'
            icon={<IconExclamationCircle />}
            title={t`No valid items selected`}
          >
            <Text>{t`Please select one or more valid assemblies to replace the component.`}</Text>
          </Alert>
        )}
        {bulkReplaceRecords?.map((record: any) => {
          return <RenderPartColumn part={record.part_detail} key={record.pk} />;
        })}
        <Divider />
      </Stack>
    ),
    fields: {
      sub_part: {
        filters: {
          active: true,
          component: true
        },
        default: partId
      }
    },
    onFormSuccess: table.refreshTable
  });

  const tableActions = useMemo(() => {
    return [
      <ActionButton
        tooltip={t`Replace Component`}
        icon={<IconReplace />}
        color='blue'
        onClick={bulkReplace.open}
        hidden={!user.hasChangeRole(UserRoles.bom)}
        disabled={!table.selectedIds.length}
      />
    ];
  }, [user, table.selectedIds]);

  return (
    <>
      {editBomItem.modal}
      {bulkReplace.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.bom_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            ...params,
            uses: partId,
            part_detail: true,
            sub_part_detail: true
          },
          enableSelection: user.hasChangeRole(UserRoles.bom),
          rowActions: rowActions,
          modelType: ModelType.part,
          modelField: 'part',
          tableActions: tableActions,
          tableFilters: tableFilters,
          isRecordSelectable: (record: any) => record.sub_part === partId
        }}
      />
    </>
  );
}
