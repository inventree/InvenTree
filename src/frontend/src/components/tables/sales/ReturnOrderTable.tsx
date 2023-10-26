import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { useMemo } from 'react';

import { renderDate } from '../../../defaults/formatters';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import { ModelType } from '../../render/ModelType';
import { TableStatusRenderer } from '../../renderers/StatusRenderer';
import { InvenTreeTable } from '../InvenTreeTable';

export function ReturnOrderTable({ params }: { params?: any }) {
  const { tableKey } = useTableRefresh('return-orders');

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
        title: t`Description`,
        switchable: true
      },
      {
        accessor: 'customer__name',
        title: t`Customer`,
        sortable: true,
        render: function (record: any) {
          let customer = record.customer_detail ?? {};

          return (
            <Group spacing="xs" noWrap={true}>
              <Thumbnail src={customer?.image} alt={customer.name} />
              <Text>{customer?.name}</Text>
            </Group>
          );
        }
      },
      {
        accessor: 'customer_reference',
        title: t`Customer Reference`,
        switchable: true
      },
      {
        accessor: 'project_code',
        title: t`Project Code`,
        switchable: true
        // TODO: Custom formatter
      },
      {
        accessor: 'status',
        title: t`Status`,
        sortable: true,
        switchable: true,
        render: TableStatusRenderer(ModelType.returnorder)
      },
      {
        accessor: 'creation_date',
        sortable: true,
        title: t`Created`,
        switchable: true,
        render: (record: any) => renderDate(record.creation_date)
      },
      {
        accessor: 'target_date',
        sortable: true,
        title: t`Target Date`,
        switchable: true,
        render: (record: any) => renderDate(record.target_date)
      }
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
        }
      }}
    />
  );
}
