import { t } from '@lingui/macro';
import {
  ActionIcon,
  CloseButton,
  Divider,
  Group,
  HoverCard,
  LoadingOverlay,
  Stack,
  Table,
  Text,
  Tooltip
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconColumnInsertLeft,
  IconFileDatabase,
  IconInfoCircle
} from '@tabler/icons-react';
import { ReactNode, useCallback, useMemo } from 'react';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useInstance } from '../../hooks/UseInstance';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { TableColumn } from '../../tables/Column';
import { TableFilter } from '../../tables/Filter';
import { InvenTreeTable } from '../../tables/InvenTreeTable';
import { StandaloneField } from '../forms/StandaloneField';

function ImporterDataField({
  field,
  row,
  session
}: {
  field: string;
  row: any;
  session: any;
}) {
  const fieldDefinition = useMemo(() => {
    const fields = session?.available_fields ?? {};

    let definition: any = undefined;

    Object.keys(fields).forEach((key) => {
      if (key == field) {
        definition = fields[key];

        definition = {
          ...definition,
          field_type: definition.type,
          description: definition.help_text,
          value: row?.data[field] ?? definition.default,
          disabled: definition.read_only ?? false
        };
      }
    });

    return definition ?? {};
  }, [session, field]);

  return (
    <td>
      {field ? (
        <StandaloneField fieldDefinition={fieldDefinition} hideLabels />
      ) : (
        <Text>field value</Text>
      )}
    </td>
  );
}

function ImporterDataRow({
  row,
  columns,
  session,
  onRowDeleted
}: {
  row: any;
  columns: any[];
  session: any;
  onRowDeleted: () => void;
}) {
  // Construct a rendering of the "original" row data
  const rowData: ReactNode = useMemo(() => {
    return (
      <Stack spacing="xs">
        <Text size="sm" weight={700}>{t`Row Data`}</Text>
        <Divider />
        {Object.keys(row.row_data).map((key) => {
          return (
            <Group spacing="xs">
              <Text size="xs" weight={700}>
                {key}
              </Text>
              <Text size="xs">{row.row_data[key]}</Text>
            </Group>
          );
        })}
      </Stack>
    );
  }, [row.row_data]);

  const removeRow = useCallback(() => {
    const url = apiUrl(ApiEndpoints.import_session_row_list, row.pk);

    api
      .delete(url)
      .then(() => {
        onRowDeleted();
      })
      .catch(() => {
        notifications.show({
          title: t`Error`,
          message: t`Could not delete row`,
          color: 'red'
        });
      });
  }, [row]);

  return (
    <tr>
      <td>
        <Group position="left">
          <Text>{row.row_index}</Text>
          <HoverCard withinPortal={true}>
            <HoverCard.Target>
              <ActionIcon size="xs">
                <IconFileDatabase />
              </ActionIcon>
            </HoverCard.Target>
            <HoverCard.Dropdown>
              <Text>{rowData}</Text>
            </HoverCard.Dropdown>
          </HoverCard>
        </Group>
      </td>
      {columns.map((column: any) => {
        return (
          <ImporterDataField field={column.field} row={row} session={session} />
        );
      })}
      <td>
        <Tooltip label={t`Remove this row`} position="left">
          <CloseButton color="red" onClick={removeRow} />
        </Tooltip>
      </td>
    </tr>
  );
}

export default function ImporterDataSelector({
  session,
  onComplete
}: {
  session: any;
  onComplete: () => void;
}) {
  const table = useTable('data-importer');

  const columns: TableColumn[] = useMemo(() => {
    let columns: TableColumn[] = [
      {
        accessor: 'row_index',
        title: t`Row`,
        sortable: true,
        switchable: false
      },
      ...session?.column_mappings
        ?.filter((column: any) => !!column.field)
        .map((column: any) => {
          return {
            accessor: column.field,
            title: column.column ?? column.title,
            sortable: false,
            switchable: true,
            render: (row: any) => {
              return (
                <ImporterDataField
                  field={column.field}
                  row={row}
                  session={session}
                />
              );
            }
          };
        })
    ];

    return columns;
  }, [session]);

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
    <Stack spacing="xs">
      <InvenTreeTable
        tableState={table}
        columns={columns}
        url={apiUrl(ApiEndpoints.import_session_row_list)}
        props={{
          params: {
            session: session.pk
          },
          tableFilters: filters,
          enableColumnSwitching: true
        }}
      />
    </Stack>
  );
}
