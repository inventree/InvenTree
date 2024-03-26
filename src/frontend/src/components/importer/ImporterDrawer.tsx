import { t } from '@lingui/macro';
import {
  Button,
  CloseButton,
  Divider,
  Drawer,
  Group,
  LoadingOverlay,
  Paper,
  Progress,
  ScrollArea,
  Space,
  Stack,
  Text
} from '@mantine/core';
import { useCallback, useMemo } from 'react';

import { getStatusCodes } from '../../components/render/StatusRenderer';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useInstance } from '../../hooks/UseInstance';
import { StylishText } from '../items/StylishText';
import { StatusRenderer, getStatusCodeName } from '../render/StatusRenderer';
import ImporterColumnSelector from './ImporterColumnSelector';

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

  const statusText = useMemo(() => {
    const status = getStatusCodeName(ModelType.importsession, session?.status);

    return status;
  }, [session]);

  const widget = useMemo(() => {
    switch (statusText) {
      case 'INITIAL':
        return <Text>Initial</Text>;
      case 'MAPPING':
        return <ImporterColumnSelector session={session} />;
      case 'IMPORTING':
        return <Text>Importing...</Text>;
      case 'PROCESSING':
        return <Text>Processing</Text>;
      case 'COMPLETE':
        return <Text>Complete!</Text>;
      default:
        return <Text>Unknown status code: {session?.status}</Text>;
    }

    return '-';
  }, [session]);

  const cancelImport = useCallback(() => {
    // TODO: Cancel import session by deleting on the server

    // Close the modal
    onClose();
  }, [session]);

  return (
    <Drawer
      position="bottom"
      size="xl"
      opened={opened}
      onClose={onClose}
      withCloseButton={false}
      closeOnEscape={false}
      closeOnClickOutside={false}
    >
      <Stack spacing="xs">
        <Group position="apart" grow>
          <StylishText size="xl">{t`Importing Data`}</StylishText>
          <Progress
            value={20}
            label={t`Mapping Columns`}
            size="20px"
            radius="md"
          />
          <Group position="right">
            <Button color="red" variant="filled" onClick={cancelImport}>
              {t`Cancel Import`}
            </Button>
          </Group>
        </Group>
        <Divider />
        <ScrollArea>
          <Stack spacing="xs">
            <LoadingOverlay visible={instanceQuery.isFetching} />
            {/* TODO: Fix the header, while the content scrolls! */}
            <Paper p="md">{instanceQuery.isFetching || widget}</Paper>
          </Stack>
        </ScrollArea>
      </Stack>
    </Drawer>
  );
}
