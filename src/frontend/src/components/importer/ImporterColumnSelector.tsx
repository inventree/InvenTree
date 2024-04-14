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
    console.log('selected column:', selectedColumn);
  }, [selectedColumn]);

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
      label={column.column}
      data={options}
      value={selectedColumn}
      onChange={onChange}
      withinPortal
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
      ...session.columnMappings.map((column: any) => {
        return {
          value: column.column,
          label: column.column
        };
      })
    ];
  }, [session.columnMappings]);

  return (
    <Stack spacing="xs">
      <Group position="apart">
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
      <SimpleGrid cols={2} spacing="xs">
        <Text weight={700}>{t`Database Field`}</Text>
        <Text weight={700}>{t`Imported Column Name`}</Text>
        <Divider />
        <Divider />
        {session.columnMappings.map((column: any) => {
          return [
            <Stack spacing="xs">
              <Text>{column.label ?? column.field}</Text>
              <Text size="sm" italic>
                {column.description}
              </Text>
            </Stack>,
            <ImporterColumn column={column} options={columnOptions} />
          ];
        })}
      </SimpleGrid>
    </Stack>
  );
}
