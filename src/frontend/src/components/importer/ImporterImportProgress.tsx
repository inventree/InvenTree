import { t } from '@lingui/macro';
import { Center, Container, Loader, Stack, Text } from '@mantine/core';
import { useInterval } from '@mantine/hooks';
import { useEffect } from 'react';

import { StylishText } from '@lib/components';
import { useStatusCodes } from '@lib/hooks';
import { ModelType } from '@lib/index';
import type { ImportSessionState } from '../../hooks/UseImportSession';

export default function ImporterImportProgress({
  session
}: Readonly<{
  session: ImportSessionState;
}>) {
  const importSessionStatus = useStatusCodes({
    modelType: ModelType.importsession
  });

  // Periodically refresh the import session data
  const interval = useInterval(() => {
    if (session.status == importSessionStatus.IMPORTING) {
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
        <Stack gap='xs'>
          <StylishText size='lg'>{t`Importing Records`}</StylishText>
          <Loader />
          <Text size='lg'>
            {t`Imported Rows`}: {session.sessionData.row_count}
          </Text>
        </Stack>
      </Container>
    </Center>
  );
}
