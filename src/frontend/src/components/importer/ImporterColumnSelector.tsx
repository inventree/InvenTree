import { t } from '@lingui/macro';
import { Button, Group, Select, Stack, Text } from '@mantine/core';
import { useMemo } from 'react';

export default function ImporterColumnSelector({ session }: { session: any }) {
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

  return (
    <Stack spacing="xs">
      <Group position="apart">
        <Text>{t`Map data columns to database fields`}</Text>
        <Button
          color="green"
          variant="filled"
        >{t`Accept Column Mapping`}</Button>
      </Group>
      {session?.column_mappings?.map((column: any) => {
        return (
          <Group position="left" grow>
            <Select label={column.column} data={fields} value={column.field} />
          </Group>
        );
      })}
    </Stack>
  );
}
