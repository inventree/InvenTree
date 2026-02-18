import { t } from '@lingui/core/macro';
import { Group, Text } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { RowEditAction, UserRoles } from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { RowAction, TableColumn } from '@lib/types/Tables';
import { formatDecimal } from '../../defaults/formatters';
import { bomItemFields } from '../../forms/BomForms';
import { useEditApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  DescriptionColumn,
  PartColumn,
  ReferenceColumn
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
      {
        accessor: 'part_detail.IPN',
        sortable: false,
        title: t`IPN`
      },
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
          hidden: locked || !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            setSelectedBomItem(record);
            editBomItem.open();
          }
        })
      ];
    },
    [user]
  );

  return (
    <>
      {editBomItem.modal}
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
          rowActions: rowActions,
          tableFilters: tableFilters,
          modelType: ModelType.part,
          modelField: 'part'
        }}
      />
    </>
  );
}
