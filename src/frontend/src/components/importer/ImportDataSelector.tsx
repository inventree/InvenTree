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
import { apiUrl } from '../../states/ApiState';
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
  const {
    instance: rows,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: ApiEndpoints.import_session_row_list,
    params: {
      session: session.pk,
      ordering: 'row_index'
    },
    hasPrimaryKey: false,
    defaultValue: [],
    refetchOnMount: true
  });

  // Select only the actively mapped columns
  const columns: any[] = useMemo(() => {
    return (session?.column_mappings ?? []).filter((column: any) => {
      return !!column.field;
    });
  }, [session]);

  return (
    <Stack spacing="xs">
      <LoadingOverlay visible={instanceQuery.isFetching} />
      <Table striped style={{ fontSize: '20%' }}>
        <thead>
          <tr>
            <th>{t`Row`}</th>
            {columns.map((column: any) => {
              return (
                <th>
                  <Tooltip
                    label={column.description}
                    hidden={!column.description}
                  >
                    <Text weight={700}>{column?.label || column?.column}</Text>
                  </Tooltip>
                </th>
              );
            })}
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rows &&
            rows.map((row: any) => {
              return (
                <ImporterDataRow
                  row={row}
                  columns={columns}
                  session={session}
                  onRowDeleted={refreshInstance}
                />
              );
            })}
        </tbody>
      </Table>
    </Stack>
  );
}
