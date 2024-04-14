import { t } from '@lingui/macro';
import {
  Button,
  Divider,
  Drawer,
  Group,
  LoadingOverlay,
  Paper,
  ScrollArea,
  Stack,
  Text
} from '@mantine/core';
import { useCallback, useMemo } from 'react';

import {
  ImportSessionStatus,
  useImportSession
} from '../../hooks/UseImportSession';
import { StylishText } from '../items/StylishText';
import ImporterDataSelector from './ImportDataSelector';
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
  const session = useImportSession({ sessionId: sessionId });

  const title: any = useMemo(() => {
    return session.sessionData?.statusText ?? t`Importing Data`;
  }, [session.sessionData]);

  const widget = useMemo(() => {
    switch (session.status) {
      case ImportSessionStatus.INITIAL:
        return <Text>Initial : TODO</Text>;
      case ImportSessionStatus.MAPPING:
        return <ImporterColumnSelector session={session} />;
      case ImportSessionStatus.IMPORTING:
        return <Text>Importing...</Text>;
      case ImportSessionStatus.PROCESSING:
        return <ImporterDataSelector session={session} />;
      case ImportSessionStatus.COMPLETE:
        return <Text>Complete!</Text>;
      default:
        return <Text>Unknown status code: {session?.status}</Text>;
    }
  }, [session]);

  const cancelImport = useCallback(() => {
    // Cancel import session by deleting on the server
    session.cancelSession();

    // Close the modal
    onClose();
  }, [session]);

  return (
    <Drawer
      position="bottom"
      size="80%"
      opened={opened}
      onClose={onClose}
      withCloseButton={false}
      closeOnEscape={false}
      closeOnClickOutside={false}
    >
      <Stack spacing="xs">
        <Group position="apart" grow>
          <StylishText size="xl">{t`Importing Data`}</StylishText>
          <StylishText size="lg">{title}</StylishText>
          <Group position="right">
            <Button color="red" variant="filled" onClick={cancelImport}>
              {t`Cancel Import`}
            </Button>
          </Group>
        </Group>
        <Divider />
        <ScrollArea>
          <Stack spacing="xs">
            <LoadingOverlay visible={session.sessionQuery.isFetching} />
            {/* TODO: Fix the header, while the content scrolls! */}
            <Paper p="md">{session.sessionQuery.isFetching || widget}</Paper>
          </Stack>
        </ScrollArea>
      </Stack>
    </Drawer>
  );
}
