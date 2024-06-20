import { t } from '@lingui/macro';
import {
  Alert,
  Button,
  Divider,
  Group,
  Select,
  SimpleGrid,
  Stack,
  Text
} from '@mantine/core';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ImportSessionState } from '../../hooks/UseImportSession';
import { apiUrl } from '../../states/ApiState';

function ImporterColumn({ column, options }: { column: any; options: any[] }) {
  const [errorMessage, setErrorMessage] = useState<string>('');

  const [selectedColumn, setSelectedColumn] = useState<string>(
    column.column ?? ''
  );

  useEffect(() => {
    setSelectedColumn(column.column ?? '');
  }, [column.column]);

  const onChange = useCallback(
    (value: any) => {
      api
        .patch(
          apiUrl(ApiEndpoints.import_session_column_mapping_list, column.pk),
          {
            column: value || ''
          }
        )
        .then((response) => {
          setSelectedColumn(response.data?.column ?? value);
          setErrorMessage('');
        })
        .catch((error) => {
          const data = error.response.data;
          setErrorMessage(
            data.column ?? data.non_field_errors ?? t`An error occurred`
          );
        });
    },
    [column]
  );

  return (
    <Select
      error={errorMessage}
      clearable
      placeholder={t`Select column, or leave blank to ignore this field.`}
      label={undefined}
      data={options}
      value={selectedColumn}
      onChange={onChange}
    />
  );
}

export default function ImporterColumnSelector({
  session
}: {
  session: ImportSessionState;
}) {
  const [errorMessage, setErrorMessage] = useState<string>('');

  const acceptMapping = useCallback(() => {
    const url = apiUrl(
      ApiEndpoints.import_session_accept_fields,
      session.sessionId
    );

    api
      .post(url)
      .then(() => {
        session.refreshSession();
      })
      .catch((error) => {
        setErrorMessage(error.response?.data?.error ?? t`An error occurred`);
      });
  }, [session.sessionId]);

  const columnOptions: any[] = useMemo(() => {
    return [
      { value: '', label: t`Ignore this field` },
      ...session.availableColumns.map((column: any) => {
        return {
          value: column,
          label: column
        };
      })
    ];
  }, [session.columnMappings]);

  return (
    <Stack gap="xs">
      <Group justify="apart">
        <Text>{t`Map data columns to database fields`}</Text>
        <Button
          color="green"
          variant="filled"
          onClick={acceptMapping}
        >{t`Accept Column Mapping`}</Button>
      </Group>
      {errorMessage && (
        <Alert color="red" title={t`Error`}>
          <Text>{errorMessage}</Text>
        </Alert>
      )}
      <SimpleGrid cols={3} spacing="xs">
        <Text fw={700}>{t`Database Field`}</Text>
        <Text fw={700}>{t`Field Description`}</Text>
        <Text fw={700}>{t`Imported Column Name`}</Text>
        <Divider />
        <Divider />
        <Divider />
        {session.columnMappings.map((column: any) => {
          return [
            <Group gap="xs">
              <Text fw={column.required ? 700 : undefined}>
                {column.label ?? column.field}
              </Text>
              {column.required && (
                <Text c="red" fw={700}>
                  *
                </Text>
              )}
            </Group>,
            <Text size="sm" fs="italic">
              {column.description}
            </Text>,
            <ImporterColumn column={column} options={columnOptions} />
          ];
        })}
      </SimpleGrid>
    </Stack>
  );
}
