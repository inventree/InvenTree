import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import type { DataTableRowExpansionProps } from 'mantine-datatable';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ProgressBar } from '../../components/items/ProgressBar';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import {
  DescriptionColumn,
  ProjectCodeColumn,
  StatusColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowViewAction } from '../RowActions';
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
        title: t`Required Stock`,
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
          order_detail: true,
          order_outstanding: true
        },
        enableSearch: false,
        enableColumnSwitching: false,
        rowExpansion: rowExpansion,
        rowActions: rowActions
      }}
    />
  );
}
