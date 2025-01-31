import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import ImporterDrawer from '../../components/importer/ImporterDrawer';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import { ProgressBar } from '../../components/items/ProgressBar';
import { RenderUser } from '../../components/render/User';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { dataImporterSessionFields } from '../../forms/ImporterForms';
import { useFilters, useUserFilters } from '../../hooks/UseFilter';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import type { TableColumn } from '../Column';
import { DateColumn, StatusColumn } from '../ColumnRenderers';
import { StatusFilterOptions, type TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction } from '../RowActions';

export default function ImportSesssionTable() {
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
