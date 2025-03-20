import { ApiEndpoints } from '@lib/core';
import { apiUrl } from '@lib/functions';
import { useTable } from '@lib/hooks';
import type { TableColumn } from '@lib/tables';
import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import { RenderUser } from '../../components/render/User';
import { DateColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export default function ExportSessionTable() {
  const table = useTable('exportsession');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'output',
        sortable: false,
        render: (record: any) => <AttachmentLink attachment={record.output} />
      },
      {
        accessor: 'output_type',
        title: t`Output Type`,
        sortable: true
      },
      {
        accessor: 'plugin',
        title: t`Plugin`,
        sortable: true
      },
      DateColumn({
        accessor: 'created',
        title: t`Exported On`,
        sortable: true
      }),
      {
        accessor: 'user',
        sortable: true,
        title: t`User`,
        render: (record: any) => RenderUser({ instance: record.user_detail })
      }
    ];
  }, []);

  return (
    <>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.data_output)}
        tableState={table}
        columns={columns}
        props={{
          enableBulkDelete: true,
          enableSelection: true,
          enableSearch: false
        }}
      />
    </>
  );
}
