import { t } from '@lingui/macro';
import { Alert, Button, Group, Select, Stack, Text } from '@mantine/core';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';

function ImporterColumn({ column, options }: { column: any; options: any }) {
  const [errorMessage, setErrorMessage] = useState<string>('');

  const [selectedField, setSelectedField] = useState<string>(
    column.field ?? ''
  );

  useEffect(() => {
    setSelectedField(column.field ?? '');
  }, [column.field]);

  const onChange = useCallback(
    (value: any) => {
      // Ignore unchanged value
      if (value == selectedField) {
        return;
      }

      api
        .patch(
          apiUrl(ApiEndpoints.import_session_column_mapping_list, column.pk),
          {
            field: value || ''
          }
        )
        .then((response) => {
          setSelectedField(response.data?.field ?? value);
          setErrorMessage('');
        })
        .catch((error) => {
          const data = error.response.data;
          setErrorMessage(
            data.field ?? data.non_field_errors ?? t`An error occurred`
          );
        });
    },
    [column]
  );

  return (
    <Select
      error={errorMessage}
      clearable
      placeholder={t`Select database field, or leave empty to ignore this column`}
      label={column.column}
      data={options}
      value={selectedField}
      onChange={onChange}
      withinPortal
    />
  );
}

export default function ImporterColumnSelector({
  session,
  onComplete
}: {
  session: any;
  onComplete: () => void;
}) {
  // Available fields
  const fields = useMemo(() => {
    const available_fields = session?.available_fields ?? {};
    let options = [];

    for (const key in available_fields) {
      let field = available_fields[key];

      if (!field.read_only) {
        options.push({
          value: key,
          label: field.label ?? key
        });
      }
    }

    return options;
  }, [session]);

  const [errorMessage, setErrorMessage] = useState<string>('');

  const acceptMapping = useCallback(() => {
    const url = apiUrl(ApiEndpoints.import_session_accept_fields, session.pk);

    api
      .post(url)
      .then((response) => {
        onComplete();
      })
      .catch((error) => {
        setErrorMessage(error.response?.data?.error ?? t`An error occurred`);
      });
  }, [session]);

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
      {session?.column_mappings?.map((column: any) => {
        return <ImporterColumn column={column} options={fields} />;
      })}
    </Stack>
  );
}
