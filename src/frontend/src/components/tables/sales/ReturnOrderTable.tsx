import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import { ModelType } from '../../render/ModelType';
import { TableStatusRenderer } from '../../renderers/StatusRenderer';
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
      },
      {
        accessor: 'description',
        title: t`Description`
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
        accessor: 'project_code',
        title: t`Project Code`

        // TODO: Custom formatter
      },
      {
        accessor: 'status',
        title: t`Status`,
        sortable: true,

        render: TableStatusRenderer(ModelType.returnorder)
      }
      // TODO: Creation date
      // TODO: Target date
      // TODO: Line items
      // TODO: Responsible
      // TODO: Total cost
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
