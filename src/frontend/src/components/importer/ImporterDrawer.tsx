import { Drawer, LoadingOverlay, Stack, Text } from '@mantine/core';
import { useMemo } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useInstance } from '../../hooks/UseInstance';

export default function ImporterDrawer({
  sessionId,
  opened,
  onClose
}: {
  sessionId: number;
  opened: boolean;
  onClose: () => void;
}) {
  const {
    instance: session,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: ApiEndpoints.import_session_list,
    pk: sessionId,
    refetchOnMount: true
  });

  // Construct list of field selections
  const fieldOptions = useMemo(() => {
    const fields = session?.available_fields ?? {};

    let options = [];

    for (const key in fields) {
      let field = fields[key];

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
    <Drawer
      position="bottom"
      size="xl"
      opened={opened}
      onClose={onClose}
      withCloseButton={false}
    >
      <Stack spacing="xs">
        <LoadingOverlay visible={instanceQuery.isFetching} />
        <Text>Model Type: {session.model_type}</Text>
        <Text>Rows: {session.row_count}</Text>
        <Text weight={700}>Columns:</Text>
        {session?.column_mappings?.map((column: any) => (
          <Text key={column.pk}>{column.column}</Text>
        ))}
      </Stack>
    </Drawer>
  );
}
