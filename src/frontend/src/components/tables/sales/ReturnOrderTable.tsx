import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { ModelType } from '../../../enums/ModelType';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import {
  CreationDateColumn,
  DescriptionColumn,
  LineItemsProgressColumn,
  ProjectCodeColumn,
  ResponsibleColumn,
  StatusColumn,
  TargetDateColumn
} from '../ColumnRenderers';
import {
  AssignedToMeFilter,
  OutstandingFilter,
  OverdueFilter,
  StatusFilterOptions,
  TableFilter
} from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export function ReturnOrderTable({ params }: { params?: any }) {
  const table = useTable('return-orders');

  const navigate = useNavigate();

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'status',
        label: t`Status`,
        description: t`Filter by order status`,
        choiceFunction: StatusFilterOptions(ModelType.returnorder)
      },
      OutstandingFilter(),
      OverdueFilter(),
      AssignedToMeFilter()
    ];
  }, []);

  // TODO: Row actions

  // TODO: Table actions (e.g. create new return order)

  const tableColumns = useMemo(() => {
    return [
      {
        accessor: 'reference',
        title: t`Return Order`,
        sortable: true
        // TODO: Display extra information if order is overdue
      },
      {
        accessor: 'customer__name',
        title: t`Customer`,
        sortable: true,
        render: function (record: any) {
          let customer = record.customer_detail ?? {};

          return (
            <Thumbnail
              src={customer?.image}
              alt={customer.name}
              text={customer.name}
            />
          );
        }
      },
      {
        accessor: 'customer_reference',
        title: t`Customer Reference`
      },
      DescriptionColumn(),
      LineItemsProgressColumn(),
      StatusColumn(ModelType.returnorder),
      ProjectCodeColumn(),
      CreationDateColumn(),
      TargetDateColumn(),
      ResponsibleColumn(),
      {
        accessor: 'total_cost',
        title: t`Total Cost`
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.return_order_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          ...params,
          customer_detail: true
        },
        customFilters: tableFilters,
        onRowClick: (row: any) => {
          if (row.pk) {
            navigate(`/sales/return-order/${row.pk}/`);
          }
        }
      }}
    />
  );
}
