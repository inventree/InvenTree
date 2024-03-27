import { t } from '@lingui/macro';
import {
  CloseButton,
  LoadingOverlay,
  Stack,
  Table,
  Text,
  Tooltip
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useCallback, useEffect, useMemo, useState } from 'react';

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

    console.log('row:', row);

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
  session,
  onRowDeleted
}: {
  row: any;
  session: any;
  onRowDeleted: () => void;
}) {
  const columns: any[] = useMemo(() => {
    return session?.column_mappings ?? [];
  }, [session]);

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
      <td>{row.row_index}</td>
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

  const columns: any[] = useMemo(() => {
    return session?.column_mappings ?? [];
  }, [session]);

  return (
    <Stack spacing="xs">
      <LoadingOverlay visible={instanceQuery.isFetching} />
      <Table striped>
        <thead>
          <tr>
            <th>{t`Row`}</th>
            {columns.map((column: any) => {
              return (
                <th>
                  <Stack spacing="xs">
                    <Text weight={700}>{column?.label || column?.column}</Text>
                    <Text size="xs">{column.description || ' '}</Text>
                  </Stack>
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
