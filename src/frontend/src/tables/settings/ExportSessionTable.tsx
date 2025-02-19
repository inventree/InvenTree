import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import { RenderUser } from '../../components/render/User';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
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
        url={apiUrl(ApiEndpoints.export_session_list)}
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
