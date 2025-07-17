import { t } from '@lingui/core/macro';
import { Group, Text } from '@mantine/core';
import type { DataTableRowExpansionProps } from 'mantine-datatable';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ProgressBar } from '@lib/components/ProgressBar';
import { RowViewAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  DescriptionColumn,
  PartColumn,
  ProjectCodeColumn,
  StatusColumn
} from '../ColumnRenderers';
import { IncludeVariantsFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import RowExpansionIcon from '../RowExpansionIcon';
import SalesOrderAllocationTable from '../sales/SalesOrderAllocationTable';

export default function PartSalesAllocationsTable({
  partId
}: Readonly<{
  partId: number;
}>) {
  const user = useUserState();
  const navigate = useNavigate();
  const table = useTable('part-sales-allocations');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'order',
        title: t`Sales Order`,
        switchable: false,
        render: (record: any) => (
          <Group wrap='nowrap' gap='xs'>
            <RowExpansionIcon
              enabled={record.allocated > 0}
              expanded={table.isRowExpanded(record.pk)}
            />
            <Text>{record.order_detail?.reference}</Text>
          </Group>
        )
      },
      DescriptionColumn({
        accessor: 'order_detail.description'
      }),
      {
        accessor: 'part_detail',
        title: t`Part`,
        render: (record: any) => <PartColumn part={record.part_detail} />
      },
      {
        accessor: 'part_detail.IPN',
        title: t`IPN`
      },
      ProjectCodeColumn({
        accessor: 'order_detail.project_code_detail'
      }),
      StatusColumn({
        accessor: 'order_detail.status',
        model: ModelType.salesorder,
        title: t`Order Status`
      }),
      {
        accessor: 'allocated',
        title: t`Allocated Stock`,
        switchable: false,
        render: (record: any) => (
          <ProgressBar
            progressLabel
            value={record.allocated}
            maximum={record.quantity}
          />
        )
      }
    ];
  }, [table.isRowExpanded]);

  const rowActions = useCallback(
    (record: any) => {
      return [
        RowViewAction({
          title: t`View Sales Order`,
          modelType: ModelType.salesorder,
          modelId: record.order,
          hidden: !user.hasViewRole(UserRoles.sales_order),
          navigate: navigate
        })
      ];
    },
    [user]
  );

  const tableFilters: TableFilter[] = useMemo(() => {
    return [IncludeVariantsFilter()];
  }, []);

  // Control row expansion
  const rowExpansion: DataTableRowExpansionProps<any> = useMemo(() => {
    return {
      allowMultiple: true,
      expandable: ({ record }: { record: any }) => {
        return table.isRowExpanded(record.pk) || record.allocated > 0;
      },
      content: ({ record }: { record: any }) => {
        return (
          <SalesOrderAllocationTable
            showOrderInfo={false}
            showPartInfo={false}
            lineItemId={record.pk}
            partId={record.part}
            allowEdit
            isSubTable
          />
        );
      }
    };
  }, [table.isRowExpanded]);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.sales_order_line_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        minHeight: 200,
        params: {
          part: partId,
          part_detail: true,
          order_detail: true,
          order_outstanding: true
        },
        tableFilters: tableFilters,
        enableSearch: false,
        enableColumnSwitching: true,
        rowExpansion: rowExpansion,
        rowActions: rowActions
      }}
    />
  );
}
