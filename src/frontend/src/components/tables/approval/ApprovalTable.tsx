import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { renderDate } from '../../../functions/formatters';
import { ownerRenderer } from '../../renderer/ownerRenderer';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

export function ApprovalTable({
  params,
  tableKey
}: {
  params: any;
  tableKey: string;
}) {
  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: `name`,
        title: t`Name`
      },
      {
        accessor: 'reference',
        title: t`Reference`,
        sortable: true
      },
      {
        accessor: 'status_text',
        title: t`Status`,
        sortable: true
      },

      {
        accessor: 'responsible',
        sortable: true,
        title: t`Responsible`,
        switchable: true,
        render: (record) => ownerRenderer(record.responsible_detail)
      },
      {
        accessor: 'finalised',
        title: t`Finalised`,
        sortable: true,
        switchable: true,
        render: (record) => (record.finalised ? t`Yes` : t`No`)
      },
      {
        accessor: 'creation_date',
        sortable: true,
        title: t`Date`,
        switchable: true,
        render: (record) => renderDate(record.creation_date)
      },
      {
        accessor: 'modified_date',
        sortable: true,
        title: t`Date`,
        switchable: true,
        render: (record) => renderDate(record.creation_date)
      },
      {
        accessor: 'finalised_date',
        sortable: true,
        title: t`Date`,
        switchable: true,
        render: (record) => renderDate(record.creation_date)
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url="/approval/"
      tableKey={tableKey}
      columns={columns}
      props={{
        enableSelection: true,
        idAccessor: 'id',
        params: params
      }}
    />
  );
}
