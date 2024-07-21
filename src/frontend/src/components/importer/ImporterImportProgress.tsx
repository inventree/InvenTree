import { t } from '@lingui/macro';
import { Center, Container, Loader, Stack, Text } from '@mantine/core';
import { useInterval } from '@mantine/hooks';
import { useEffect } from 'react';

import {
  ImportSessionState,
  ImportSessionStatus
} from '../../hooks/UseImportSession';
import { StylishText } from '../items/StylishText';

export default function ImporterImportProgress({
  session
}: {
  session: ImportSessionState;
}) {
  // Periodically refresh the import session data
  const interval = useInterval(() => {
    console.log('refreshing:', session.status);

    if (session.status == ImportSessionStatus.IMPORTING) {
      session.refreshSession();
    }
  }, 1000);

  useEffect(() => {
    interval.start();
    return interval.stop;
  }, []);

  return (
    <Center>
      <Container>
        <Stack gap="xs">
          <StylishText size="lg">{t`Importing Records`}</StylishText>
          <Loader />
          <Text size="lg">
            {t`Imported rows`}: {session.sessionData.row_count}
          </Text>
        </Stack>
      </Container>
    </Center>
  );
}
