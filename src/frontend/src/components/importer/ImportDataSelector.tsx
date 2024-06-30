import { t } from '@lingui/macro';
import { Group, HoverCard, Stack, Text } from '@mantine/core';
import { IconCircleCheck, IconExclamationCircle } from '@tabler/icons-react';
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
  session,
  column,
  row,
  onEdit
}: {
  session: ImportSessionState;
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
    if (!row.errors) {
      return [];
    }
    return row?.errors[column.field] ?? [];
  }, [row.errors, column.field]);

  const cellValue = useMemo(() => {
    // TODO: Render inline models, rather than raw PK values

    return row.data ? row.data[column.field] : '';
  }, [row.data, column.field, session.availableFields]);

  const cellValid: boolean = useMemo(
    () => cellErrors.length == 0,
    [cellErrors]
  );

  return (
    <HoverCard disabled={cellValid} openDelay={100} closeDelay={100}>
      <HoverCard.Target>
        <Group grow justify="apart" onClick={onRowEdit}>
          <Group grow style={{ flex: 1 }}>
            <Text c={cellValid ? undefined : 'red'}>{cellValue}</Text>
          </Group>
        </Group>
      </HoverCard.Target>
      <HoverCard.Dropdown>
        <Stack gap="xs">
          {cellErrors.map((error: string) => (
            <Text size="xs" c="red" key={error}>
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
}: {
  session: ImportSessionState;
}) {
  const table = useTable('dataimporter');

  const [selectedFieldNames, setSelectedFieldNames] = useState<string[]>([]);

  const selectedFields: ApiFormFieldSet = useMemo(() => {
    let fields: ApiFormFieldSet = {};

    for (let field of selectedFieldNames) {
      // Find the field definition in session.availableFields
      let fieldDef = session.availableFields[field];
      if (fieldDef) {
        fields[field] = {
          ...fieldDef,
          field_type: fieldDef.type,
          description: fieldDef.help_text
        };
      }
    }

    return fields;
  }, [selectedFieldNames, session.availableFields]);

  const [selectedRow, setSelectedRow] = useState<any>({});

  const editCell = useCallback(
    (row: any, col: any) => {
      setSelectedRow(row);
      setSelectedFieldNames([col.field]);
      editRow.open();
    },
    [session]
  );

  const editRow = useEditApiFormModal({
    url: ApiEndpoints.import_session_row_list,
    pk: selectedRow.pk,
    title: t`Edit Data`,
    fields: selectedFields,
    initialData: selectedRow.data,
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

  const deleteRow = useDeleteApiFormModal({
    url: ApiEndpoints.import_session_row_list,
    pk: selectedRow.pk,
    title: t`Delete Row`,
    onFormSuccess: () => table.refreshTable()
  });

  const rowErrors = useCallback((row: any) => {
    if (!row.errors) {
      return [];
    }

    let errors: string[] = [];

    for (const k of Object.keys(row.errors)) {
      row.errors[k].forEach((e: string) => {
        errors.push(`${k}: ${e}`);
      });
    }

    return errors;
  }, []);

  const columns: TableColumn[] = useMemo(() => {
    let columns: TableColumn[] = [
      {
        accessor: 'row_index',
        title: t`Row`,
        sortable: true,
        switchable: false,
        render: (row: any) => {
          return (
            <Group justify="left" gap="xs">
              <Text size="sm">{row.row_index}</Text>
              {row.valid ? (
                <IconCircleCheck color="green" size={16} />
              ) : (
                <HoverCard openDelay={50} closeDelay={100}>
                  <HoverCard.Target>
                    <IconExclamationCircle color="red" size={16} />
                  </HoverCard.Target>
                  <HoverCard.Dropdown>
                    <Stack gap="xs">
                      {rowErrors(row).map((error: string) => (
                        <Text size="xs" c="red" key={error}>
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
          title: column.column ?? column.title,
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
    (record: any) => {
      return [
        RowEditAction({
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
      <Stack gap="xs">
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
            enableColumnSwitching: true,
            enableColumnCaching: false,
            enableSelection: true
          }}
        />
      </Stack>
    </>
  );
}
