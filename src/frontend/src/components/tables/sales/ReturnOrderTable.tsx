import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import { ProgressBar } from '../../items/ProgressBar';
import { ModelType } from '../../render/ModelType';
import { TableStatusRenderer } from '../../renderers/StatusRenderer';
import {
  CreationDateColumn,
  DescriptionColumn,
  ProjectCodeColumn,
  ResponsibleColumn,
  StatusColumn,
  TargetDateColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export function ReturnOrderTable({ params }: { params?: any }) {
  const { tableKey } = useTableRefresh('return-orders');

  const navigate = useNavigate();

  // TODO: Custom filters

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
      {
        accessor: 'line_items',
        title: t`Line Items`,
        sortable: true,
        render: (record: any) => (
          <ProgressBar
            value={record.completed_lines}
            maximum={record.line_items}
            progressLabel={true}
          />
        )
      },
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
      tableKey={tableKey}
      columns={tableColumns}
      props={{
        params: {
          ...params,
          customer_detail: true
        },
        onRowClick: (row: any) => {
          if (row.pk) {
            navigate(`/sales/return-order/${row.pk}/`);
          }
        }
      }}
    />
  );
}
