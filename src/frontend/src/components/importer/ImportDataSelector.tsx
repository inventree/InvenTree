import { t } from '@lingui/macro';
import { ActionIcon, Group, Stack, Text, Tooltip } from '@mantine/core';
import {
  IconCircleCheck,
  IconEdit,
  IconExclamationCircle
} from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { cancelEvent } from '../../functions/events';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { ImportSessionState } from '../../hooks/UseImportSession';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { TableColumn } from '../../tables/Column';
import { TableFilter } from '../../tables/Filter';
import { InvenTreeTable } from '../../tables/InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../../tables/RowActions';
import { ApiFormFieldSet } from '../forms/fields/ApiFormField';

function ImporterDataCell({
  column,
  row,
  onEdit
}: {
  column: any;
  row: any;
  onEdit?: () => void;
}) {
  const onRowEdit = useCallback(
    (event: any) => {
      cancelEvent(event);
      onEdit?.();
    },
    [onEdit]
  );

  const cellErrors: string[] = useMemo(() => {
    return row?.errors[column.field] ?? [];
  }, [row.errors, column.field]);

  return (
    <Group grow position="apart">
      <Group grow style={{ flex: 1 }}>
        <Stack spacing="xs">
          <Text>{row.data[column.field]}</Text>
          {cellErrors.map((error: string) => (
            <Text size="xs" color="red">
              {error}
            </Text>
          ))}
        </Stack>
      </Group>
      <div style={{ flex: 0 }}>
        <Tooltip label={t`Edit cell`}>
          <ActionIcon size="xs" onClick={onRowEdit}>
            <IconEdit />
          </ActionIcon>
        </Tooltip>
      </div>
    </Group>
  );
}

export default function ImporterDataSelector({
  session
}: {
  session: ImportSessionState;
}) {
  const table = useTable('data-importer');

  const rowEditFields: ApiFormFieldSet = useMemo(() => {
    // TODO: Construct a set of fields based on the provided session information
    return {};
  }, [session]);

  const [selectedFields, setSelectedFields] = useState<ApiFormFieldSet>({});

  const [selectedRow, setSelectedRow] = useState<number>(0);

  const editRow = useEditApiFormModal({
    url: ApiEndpoints.import_session_row_list,
    pk: selectedRow,
    title: t`Edit Data`,
    fields: selectedFields,
    onFormSuccess: (row: any) => table.updateRecord(row)
  });

  const deleteRow = useDeleteApiFormModal({
    url: ApiEndpoints.import_session_row_list,
    pk: selectedRow,
    title: t`Delete Row`,
    onFormSuccess: () => table.refreshTable()
  });

  const editCell = useCallback(
    (row: any, col: any) => {
      setSelectedRow(row.pk);
      // TODO: Set selected fields only for the selected column
      setSelectedFields({});
      editRow.open();
    },
    [session]
  );

  const columns: TableColumn[] = useMemo(() => {
    let columns: TableColumn[] = [
      {
        accessor: 'row_index',
        title: t`Row`,
        sortable: true,
        switchable: false,
        render: (row: any) => {
          return (
            <Group position="left" spacing="xs">
              <Text size="sm">{row.row_index}</Text>
              {row.valid ? (
                <IconCircleCheck color="green" size={12} />
              ) : (
                <IconExclamationCircle color="red" size={12} />
              )}
            </Group>
          );
        }
      },
      ...session.sessionData?.column_mappings
        ?.filter((column: any) => !!column.field)
        .map((column: any) => {
          return {
            accessor: column.field,
            title: column.column ?? column.title,
            sortable: false,
            switchable: true,
            render: (row: any) => {
              return (
                <ImporterDataCell
                  column={column}
                  row={row}
                  onEdit={() => editCell(row, column)}
                />
              );
            }
          };
        })
    ];

    return columns;
  }, [session]);

  const rowActions = useCallback(
    (record: any) => {
      return [
        RowEditAction({
          onClick: () => {
            setSelectedRow(record.pk);
            editRow.open();
          }
        }),
        RowDeleteAction({
          onClick: () => {
            setSelectedRow(record.pk);
            deleteRow.open();
          }
        })
      ];
    },
    [session]
  );

  const filters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'valid',
        label: t`Valid`,
        description: t`Filter by row validation status`,
        type: 'boolean'
      },
      {
        name: 'complete',
        label: t`Complete`,
        description: t`Filter by row completion status`,
        type: 'boolean'
      }
    ];
  }, []);

  return (
    <>
      {editRow.modal}
      {deleteRow.modal}
      <Stack spacing="xs">
        <InvenTreeTable
          tableState={table}
          columns={columns}
          url={apiUrl(ApiEndpoints.import_session_row_list)}
          props={{
            params: {
              session: session.sessionId
            },
            rowActions: rowActions,
            tableFilters: filters,
            enableColumnSwitching: true
          }}
        />
      </Stack>
    </>
  );
}
