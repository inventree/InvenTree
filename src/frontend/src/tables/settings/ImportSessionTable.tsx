import { t } from '@lingui/macro';
import { useCallback, useMemo } from 'react';

import { AttachmentLink } from '../../components/items/AttachmentLink';
import { ProgressBar } from '../../components/items/ProgressBar';
import { RenderUser } from '../../components/render/User';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useFilters, useUserFilters } from '../../hooks/UseFilter';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { DateColumn, StatusColumn } from '../ColumnRenderers';
import { StatusFilterOptions, TableFilter } from '../Filter';
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

  const userFilter = useUserFilters();

  const modelTypeFilters = useFilters({
    url: apiUrl(ApiEndpoints.import_session_list),
    method: 'OPTIONS',
    accessor: 'data.actions.POST.model_type.choices',
    transform: (item: any) => {
      return {
        value: item.value,
        label: item.display_name
      };
    }
  });

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'model_type',
        label: t`Model Type`,
        description: t`Filter by target model type`,
        choices: modelTypeFilters.choices
      },
      {
        name: 'status',
        label: t`Status`,
        description: t`Filter by import session status`,
        choiceFunction: StatusFilterOptions(ModelType.importsession)
      },
      {
        name: 'user',
        label: t`User`,
        description: t`Filter by user`,
        choices: userFilter.choices
      }
    ];
  }, [modelTypeFilters.choices, userFilter.choices]);

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
          tableActions: tableActions,
          tableFilters: tableFilters
        }}
      />
    </>
  );
}
