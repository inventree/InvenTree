import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { ProgressBar } from '@lib/components/ProgressBar';
import { type RowAction, RowDeleteAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import ImporterDrawer from '../../components/importer/ImporterDrawer';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import { RenderUser } from '../../components/render/User';
import { dataImporterSessionFields } from '../../forms/ImporterForms';
import { useFilters } from '../../hooks/UseFilter';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { DateColumn, StatusColumn } from '../ColumnRenderers';
import { StatusFilterOptions, UserFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export default function ImportSessionTable() {
  const table = useTable('importsession');

  const [opened, setOpened] = useState<boolean>(false);

  const [selectedSession, setSelectedSession] = useState<number | undefined>(
    undefined
  );

  const deleteSession = useDeleteApiFormModal({
    url: ApiEndpoints.import_session_list,
    pk: selectedSession,
    title: t`Delete Import Session`,
    table: table
  });

  const newImportSession = useCreateApiFormModal({
    url: ApiEndpoints.import_session_list,
    title: t`Create Import Session`,
    fields: dataImporterSessionFields(),
    onFormSuccess: (response: any) => {
      setSelectedSession(response.pk);
      setOpened(true);
      table.refreshTable();
    }
  });

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'model_type',
        sortable: true
      },
      StatusColumn({ model: ModelType.importsession, accessor: 'status' }),
      {
        accessor: 'data_file',
        render: (record: any) => (
          <AttachmentLink attachment={record.data_file} />
        ),
        sortable: false,
        noContext: true
      },
      DateColumn({
        accessor: 'timestamp',
        title: t`Uploaded`
      }),
      {
        accessor: 'user',
        sortable: false,
        title: t`User`,
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
      UserFilter({})
    ];
  }, [modelTypeFilters.choices]);

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='create-import-session'
        tooltip={t`Create Import Session`}
        onClick={() => newImportSession.open()}
      />
    ];
  }, []);

  const rowActions = useCallback((record: any): RowAction[] => {
    return [
      RowDeleteAction({
        onClick: () => {
          setSelectedSession(record.pk);
          deleteSession.open();
        }
      })
    ];
  }, []);

  return (
    <>
      {newImportSession.modal}
      {deleteSession.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.import_session_list)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions,
          tableFilters: tableFilters,
          enableBulkDelete: true,
          enableSelection: true,
          onRowClick: (record: any) => {
            setSelectedSession(record.pk);
            setOpened(true);
          }
        }}
      />
      <ImporterDrawer
        sessionId={selectedSession ?? -1}
        opened={selectedSession !== undefined && opened}
        onClose={() => {
          setSelectedSession(undefined);
          setOpened(false);
          table.refreshTable();
        }}
      />
    </>
  );
}
