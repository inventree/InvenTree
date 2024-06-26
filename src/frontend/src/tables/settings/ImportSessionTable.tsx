import { t } from '@lingui/macro';
import { useCallback, useMemo } from 'react';

import { AttachmentLink } from '../../components/items/AttachmentLink';
import { ProgressBar } from '../../components/items/ProgressBar';
import { RenderUser } from '../../components/render/User';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { DateColumn, StatusColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction } from '../RowActions';

export default function ImportSesssionTable() {
  const table = useTable('importsession');
  const user = useUserState();

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'model_type',
        sortable: true
      },
      StatusColumn({ model: ModelType.importsession }),
      {
        accessor: 'data_file',
        render: (record: any) => (
          <AttachmentLink attachment={record.data_file} />
        ),
        sortable: false
      },
      DateColumn({
        accessor: 'timestamp',
        title: t`Uploaded`
      }),
      {
        accessor: 'user',
        sortable: false,
        render: (record: any) => RenderUser({ instance: record.user_detail })
      },
      {
        sortable: false,
        accessor: 'row_count',
        title: t`Imported Rows`,
        render: (record: any) => (
          <ProgressBar
            progressLabel={true}
            value={record.completed_row_count}
            maximum={record.row_count}
          />
        )
      }
    ];
  }, []);

  const tableActions = useMemo(() => {
    return [];
  }, []);

  const rowActions = useCallback((record: any): RowAction[] => {
    return [];
  }, []);

  return (
    <>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.import_session_list)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions
        }}
      />
    </>
  );
}
