import { t } from '@lingui/core/macro';
import {
  Alert,
  Button,
  Group,
  Paper,
  Select,
  Space,
  Stack,
  Table,
  Text
} from '@mantine/core';
import { IconCheck } from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { ApiFormFieldType } from '@lib/types/Forms';
import { useDebouncedValue } from '@mantine/hooks';
import { useApi } from '../../contexts/ApiContext';
import type { ImportSessionState } from '../../hooks/UseImportSession';
import { StandaloneField } from '../forms/StandaloneField';

function ImporterColumn({
  column,
  options
}: Readonly<{ column: any; options: any[] }>) {
  const api = useApi();

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
      aria-label={`import-column-map-${column.field}`}
      error={errorMessage}
      clearable
      searchable
      placeholder={t`Select column, or leave blank to ignore this field.`}
      label={undefined}
      data={options}
      value={selectedColumn}
      onChange={onChange}
    />
  );
}

function ImporterDefaultField({
  fieldName,
  session
}: {
  fieldName: string;
  session: ImportSessionState;
}) {
  const api = useApi();

  const [rawValue, setRawValue] = useState<any>(undefined);

  // Initialize raw value with provided default
  useEffect(() => {
    setRawValue(session.fieldDefaults[fieldName]);
  }, [fieldName, session.fieldDefaults]);

  const fieldType: string = useMemo(() => {
    return session.availableFields[fieldName]?.type;
  }, [fieldName, session.availableFields]);

  const onChange = useCallback(
    (value: any) => {
      if (value === undefined) {
        value = session.fieldDefaults[fieldName];
      }

      // No change - do nothing
      if (value === session.fieldDefaults[fieldName]) {
        return;
      }

      // Update the default value for the field
      const defaults = {
        ...session.fieldDefaults,
        [fieldName]: value
      };

      api
        .patch(apiUrl(ApiEndpoints.import_session_list, session.sessionId), {
          field_defaults: defaults
        })
        .then((response: any) => {
          session.setSessionData(response.data);
        })
        .catch(() => {
          // TODO: Error message?
        });
    },
    [fieldName, session, session.fieldDefaults]
  );

  const getDebounceTime = (type: string) => {
    switch (type) {
      case 'string':
        return 500;
      case 'number':
      case 'float':
      case 'integer':
        return 200;
      default:
        return 50;
    }
  };

  const [value] = useDebouncedValue(rawValue, getDebounceTime(fieldType));

  // Update the default value after the debounced value changes
  useEffect(() => {
    onChange(value);
  }, [value]);

  const fieldDef: ApiFormFieldType = useMemo(() => {
    let def: any = session.availableFields[fieldName];

    if (def) {
      def = {
        ...def,
        value: session.fieldDefaults[fieldName],
        field_type: def.type,
        description: def.help_text,
        required: false,
        onValueChange: (value: string) => {
          setRawValue(value);
        }
      };
    }

    return def;
  }, [fieldName, session.availableFields, session.fieldDefaults]);

  return (
    fieldDef && <StandaloneField fieldDefinition={fieldDef} hideLabels={true} />
  );
}

function ImporterColumnTableRow({
  session,
  column,
  options
}: Readonly<{
  session: ImportSessionState;
  column: any;
  options: any;
}>) {
  return (
    <Table.Tr key={column.label ?? column.field}>
      <Table.Td>
        <Group gap='xs'>
          <Text fw={column.required ? 700 : undefined}>
            {column.label ?? column.field}
          </Text>
          {column.required && (
            <Text c='red' fw={700}>
              *
            </Text>
          )}
        </Group>
      </Table.Td>
      <Table.Td>
        <Text size='sm'>{column.description}</Text>
      </Table.Td>
      <Table.Td>
        <ImporterColumn column={column} options={options} />
      </Table.Td>
      <Table.Td>
        <ImporterDefaultField fieldName={column.field} session={session} />
      </Table.Td>
    </Table.Tr>
  );
}

export default function ImporterColumnSelector({
  session
}: Readonly<{
  session: ImportSessionState;
}>) {
  const api = useApi();

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
  }, [session.availableColumns]);

  return (
    <Stack gap='xs'>
      <Paper shadow='xs' p='xs'>
        <Group grow justify='apart'>
          <Text size='lg'>{t`Mapping data columns to database fields`}</Text>
          <Space />
          <Button color='green' variant='filled' onClick={acceptMapping}>
            <Group>
              <IconCheck />
              {t`Accept Column Mapping`}
            </Group>
          </Button>
        </Group>
      </Paper>
      {errorMessage && (
        <Alert color='red' title={t`Error`}>
          <Text>{errorMessage}</Text>
        </Alert>
      )}
      <Table>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>{t`Database Field`}</Table.Th>
            <Table.Th>{t`Field Description`}</Table.Th>
            <Table.Th>{t`Imported Column`}</Table.Th>
            <Table.Th>{t`Default Value`}</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {session.columnMappings.map((column: any) => {
            return (
              <ImporterColumnTableRow
                key={`import-${column.field}}`}
                session={session}
                column={column}
                options={columnOptions}
              />
            );
          })}
        </Table.Tbody>
      </Table>
    </Stack>
  );
}
