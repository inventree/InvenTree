import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import { ProgressBar } from '../../items/ProgressBar';
import { ModelType } from '../../render/ModelType';
import { TableStatusRenderer } from '../../renderers/StatusRenderer';
import { InvenTreeTable } from '../InvenTreeTable';
import { ProjectCodeHoverCard } from '../TableHoverCard';

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
      {
        accessor: 'description',
        title: t`Description`
      },
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
      {
        accessor: 'project_code',
        title: t`Project Code`,
        render: (record: any) => (
          <ProjectCodeHoverCard projectCode={record.project_code_detail} />
        )
      },
      {
        accessor: 'status',
        title: t`Status`,
        sortable: true,
        render: TableStatusRenderer(ModelType.returnorder)
      },
      {
        accessor: 'creation_date',
        title: t`Creation Date`
      },
      {
        accessor: 'target_date',
        title: t`Target Date`
      },
      {
        accessor: 'responsible',
        title: t`Responsible`,
        render: TableStatusRenderer(ModelType.owner)
      },
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
