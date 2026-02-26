import { t } from '@lingui/core/macro';
import { Group, HoverCard, Paper, Space, Stack, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconArrowRight,
  IconCircleCheck,
  IconCircleDashedCheck,
  IconExclamationCircle
} from '@tabler/icons-react';
import { type ReactNode, useCallback, useMemo, useState } from 'react';

import { ActionButton } from '@lib/components/ActionButton';
import { ProgressBar } from '@lib/components/ProgressBar';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { YesNoButton } from '@lib/components/YesNoButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { cancelEvent } from '@lib/functions/Events';
import type { TableFilter } from '@lib/types/Filters';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { useApi } from '../../contexts/ApiContext';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import type { ImportSessionState } from '../../hooks/UseImportSession';
import { useTable } from '../../hooks/UseTable';
import { InvenTreeTable } from '../../tables/InvenTreeTable';
import { RenderRemoteInstance } from '../render/Instance';

function ImporterDataCell({
  session,
  column,
  row,
  onEdit
}: Readonly<{
  session: ImportSessionState;
  column: any;
  row: any;
  onEdit?: () => void;
}>) {
  const onRowEdit = useCallback(
    (event: any) => {
      cancelEvent(event);

      if (!row.complete) {
        onEdit?.();
      }
    },
    [onEdit, row]
  );

  const cellErrors: string[] = useMemo(() => {
    if (!row.errors) {
      return [];
    }
    return row?.errors[column.field] ?? [];
  }, [row.errors, column.field]);

  const cellValue: ReactNode = useMemo(() => {
    const field_def = session.availableFields[column.field];

    if (!row?.data) {
      return '-';
    }

    switch (field_def?.type) {
      case 'boolean':
        return (
          <YesNoButton value={row.data ? row.data[column.field] : false} />
        );
      case 'related field':
        if (field_def.model && row.data[column.field]) {
          return (
            <RenderRemoteInstance
              model={field_def.model}
              pk={row.data[column.field]}
            />
          );
        }
        break;
      default:
        break;
    }

    let value = row.data ? (row.data[column.field] ?? '') : '';

    if (!value) {
      value = '-';
    }

    return value;
  }, [row.data, column.field, session.availableFields]);

  const cellValid: boolean = useMemo(
    () => cellErrors.length == 0,
    [cellErrors]
  );

  return (
    <HoverCard disabled={cellValid} openDelay={100} closeDelay={100}>
      <HoverCard.Target>
        <Group grow justify='apart' onClick={onRowEdit}>
          <Group grow style={{ flex: 1 }}>
            <Text size='xs' c={cellValid ? undefined : 'red'}>
              {cellValue}
            </Text>
          </Group>
        </Group>
      </HoverCard.Target>
      <HoverCard.Dropdown>
        <Stack gap='xs'>
          {cellErrors.map((error: string) => (
            <Text size='xs' c='red' key={error}>
              {error}
            </Text>
          ))}
        </Stack>
      </HoverCard.Dropdown>
    </HoverCard>
  );
}

export default function ImporterDataSelector({
  session
}: Readonly<{
  session: ImportSessionState;
}>) {
  const api = useApi();
  const table = useTable('dataimporter');

  const [selectedFieldNames, setSelectedFieldNames] = useState<string[]>([]);

  const selectedFields: ApiFormFieldSet = useMemo(() => {
    const fields: ApiFormFieldSet = {};

    for (const field of selectedFieldNames) {
      // Find the field definition in session.availableFields
      const fieldDef = session.availableFields[field];
      if (fieldDef) {
        // Construct field filters based on session field filters
        let filters = fieldDef.filters ?? {};

        if (session.fieldFilters[field]) {
          filters = {
            ...filters,
            ...session.fieldFilters[field]
          };
        }

        if (field == 'id') {
          continue; // Skip the ID field
        }

        fields[field] = {
          ...fieldDef,
          field_type: fieldDef.type,
          description: fieldDef.help_text,
          filters: filters
        };
      }
    }

    return fields;
  }, [selectedFieldNames, session.availableFields, session.fieldFilters]);

  const importData = useCallback(
    (rows: number[]) => {
      notifications.show({
        title: t`Importing Rows`,
        message: t`Please wait while the data is imported`,
        autoClose: false,
        color: 'blue',
        id: 'importing-rows',
        icon: <IconArrowRight />
      });

      api
        .post(
          apiUrl(ApiEndpoints.import_session_accept_rows, session.sessionId),
          {
            rows: rows
          }
        )
        .catch(() => {
          notifications.show({
            title: t`Error`,
            message: t`An error occurred while importing data`,
            color: 'red',
            autoClose: true
          });
        })
        .finally(() => {
          table.clearSelectedRecords();
          notifications.hide('importing-rows');
          table.refreshTable();

          session.refreshSession();
        });
    },
    [session.sessionId, table.refreshTable]
  );

  const [selectedRow, setSelectedRow] = useState<any>({});

  const editRow = useEditApiFormModal({
    url: ApiEndpoints.import_session_row_list,
    pk: selectedRow.pk,
    title: t`Edit Data`,
    fields: selectedFields,
    initialData: selectedRow.data,
    fetchInitialData: false,
    processFormData: (data: any) => {
      // Construct fields back into a single object
      return {
        data: {
          ...selectedRow.data,
          ...data
        }
      };
    },
    onFormSuccess: (row: any) => table.updateRecord(row)
  });

  const editCell = useCallback(
    (row: any, col: any) => {
      if (col.field == 'id') {
        return; // Cannot edit the ID field
      }

      setSelectedRow(row);
      setSelectedFieldNames([col.field]);
      editRow.open();
    },
    [session, editRow]
  );

  const deleteRow = useDeleteApiFormModal({
    url: ApiEndpoints.import_session_row_list,
    pk: selectedRow.pk,
    title: t`Delete Row`,
    onFormSuccess: () => {
      table.clearSelectedRecords();
      table.refreshTable();
      session.refreshSession();
    }
  });

  const rowErrors = useCallback((row: any) => {
    if (!row.errors) {
      return [];
    }

    const errors: string[] = [];

    for (const k of Object.keys(row.errors)) {
      if (row.errors[k]) {
        if (Array.isArray(row.errors[k])) {
          row.errors[k].forEach((e: string) => {
            errors.push(`${k}: ${e}`);
          });
        } else {
          errors.push(row.errors[k].toString());
        }
      }
    }

    return errors;
  }, []);

  const columns: TableColumn[] = useMemo(() => {
    const columns: TableColumn[] = [
      {
        accessor: 'row_index',
        title: t`Row`,
        sortable: true,
        switchable: false,
        render: (row: any) => {
          return (
            <Group justify='left' gap='xs'>
              <Text size='sm'>{row.row_index}</Text>
              {row.complete && <IconCircleCheck color='green' size={16} />}
              {!row.complete && row.valid && (
                <IconCircleDashedCheck color='blue' size={16} />
              )}
              {!row.complete && !row.valid && (
                <HoverCard openDelay={50} closeDelay={100} position='top-start'>
                  <HoverCard.Target>
                    <IconExclamationCircle color='red' size={16} />
                  </HoverCard.Target>
                  <HoverCard.Dropdown>
                    <Stack gap='xs'>
                      <Text>{t`Row contains errors`}:</Text>
                      {rowErrors(row).map((error: string) => (
                        <Text size='sm' c='red' key={error}>
                          {error}
                        </Text>
                      ))}
                    </Stack>
                  </HoverCard.Dropdown>
                </HoverCard>
              )}
            </Group>
          );
        }
      },
      ...session.mappedFields.map((column: any) => {
        return {
          accessor: column.field,
          title: column.label ?? column.column,
          sortable: false,
          switchable: true,
          render: (row: any) => {
            return (
              <ImporterDataCell
                session={session}
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
    (record: any): RowAction[] => {
      return [
        {
          title: t`Accept`,
          icon: <IconArrowRight />,
          color: 'green',
          hidden: record.complete || !record.valid,
          onClick: () => {
            importData([record.pk]);
          }
        },
        RowEditAction({
          hidden: record.complete,
          onClick: () => {
            setSelectedRow(record);
            setSelectedFieldNames(
              session.mappedFields.map((f: any) => f.field)
            );
            editRow.open();
          }
        }),
        RowDeleteAction({
          onClick: () => {
            setSelectedRow(record);
            deleteRow.open();
          }
        })
      ];
    },
    [session, importData]
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

  const tableActions = useMemo(() => {
    // Can only "import" valid (and incomplete) rows
    const canImport: boolean =
      table.hasSelectedRecords &&
      table.selectedRecords.every((row: any) => row.valid && !row.complete);

    return [
      <ActionButton
        key='import-selected-rows'
        disabled={!canImport}
        icon={<IconArrowRight />}
        color='green'
        tooltip={t`Import selected rows`}
        onClick={() => {
          importData(table.selectedRecords.map((row: any) => row.pk));
        }}
      />
    ];
  }, [table.hasSelectedRecords, table.selectedRecords]);

  return (
    <>
      {editRow.modal}
      {deleteRow.modal}
      <Stack gap='xs'>
        <Paper shadow='xs' p='xs'>
          <Group grow justify='apart'>
            <Text size='lg'>{t`Processing Data`}</Text>
            <Space />
            <ProgressBar
              maximum={session.rowCount}
              value={session.completedRowCount}
              progressLabel
            />
            <Space />
          </Group>
        </Paper>
        <InvenTreeTable
          tableState={table}
          columns={columns}
          url={apiUrl(ApiEndpoints.import_session_row_list)}
          props={{
            params: {
              session: session.sessionId
            },
            rowActions: rowActions,
            tableActions: tableActions,
            tableFilters: filters,
            enableColumnSwitching: true,
            enableColumnCaching: false,
            enableSelection: true,
            enableBulkDelete: true,
            afterBulkDelete: () => {
              table.clearSelectedRecords();
              table.refreshTable();
              session.refreshSession();
            }
          }}
        />
      </Stack>
    </>
  );
}
