import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { t } from '@lingui/core/macro';
import { useMemo } from 'react';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import { RenderUser } from '../../components/render/User';
import { useTable } from '../../hooks/UseTable';
import type { TableColumn } from '../Column';
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
