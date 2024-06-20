import { t } from '@lingui/macro';
import {
  ActionIcon,
  Button,
  Divider,
  Drawer,
  Group,
  LoadingOverlay,
  Paper,
  ScrollArea,
  Stack,
  Text,
  Tooltip
} from '@mantine/core';
import { IconCircleX } from '@tabler/icons-react';
import { ReactNode, useCallback, useMemo } from 'react';

import {
  ImportSessionStatus,
  useImportSession
} from '../../hooks/UseImportSession';
import { ProgressBar } from '../items/ProgressBar';
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

  const description: string = useMemo(() => {
    switch (session.status) {
      case ImportSessionStatus.INITIAL:
        return t`Data File Upload`;
      case ImportSessionStatus.MAPPING:
        return t`Mapping Data Columns`;
      case ImportSessionStatus.IMPORTING:
        return t`Importing Data`;
      case ImportSessionStatus.PROCESSING:
        return t`Processing Data`;
      case ImportSessionStatus.COMPLETE:
        return t`Import Complete`;
      default:
        return t`Unknown Status` + ` - ${session.status}`;
    }
  }, [session]);

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

  const title: ReactNode = useMemo(() => {
    return (
      <Stack gap="xs" style={{ width: '100%' }}>
        <Group
          gap="xs"
          wrap="nowrap"
          grow
          justify="space-between"
          preventGrowOverflow={false}
        >
          <StylishText>
            {session.sessionData?.statusText ?? t`Importing Data`}
          </StylishText>
          <Stack gap="xs">
            <Text size="sm">{description}</Text>
            <ProgressBar value={0} maximum={5} />
          </Stack>
          <Tooltip label={t`Cancel Import`}>
            <ActionIcon color="red" onClick={cancelImport}>
              <IconCircleX />
            </ActionIcon>
          </Tooltip>
        </Group>
        <Divider />
      </Stack>
    );
  }, []);

  return (
    <Drawer
      position="bottom"
      size="80%"
      title={title}
      opened={opened}
      onClose={onClose}
      withCloseButton={false}
      closeOnEscape={false}
      closeOnClickOutside={false}
      styles={{
        header: {
          width: '90%'
        },
        title: {
          width: '100%'
        }
      }}
    >
      <Stack gap="xs">
        <LoadingOverlay visible={session.sessionQuery.isFetching} />
        <Paper p="md">{session.sessionQuery.isFetching || widget}</Paper>
      </Stack>
    </Drawer>
  );
}
