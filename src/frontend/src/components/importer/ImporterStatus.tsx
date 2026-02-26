import { t } from '@lingui/core/macro';
import { Center, Loader, Stack } from '@mantine/core';
import { useInterval } from '@mantine/hooks';
import { useMemo } from 'react';

import { ModelType } from '@lib/enums/ModelType';
import type { ImportSessionState } from '../../hooks/UseImportSession';
import { StylishText } from '../items/StylishText';
import { getStatusCodeLabel } from '../render/StatusRenderer';

export default function ImporterStatus({
  session
}: Readonly<{
  session: ImportSessionState;
}>) {
  const statusText = useMemo(() => {
    return (
      getStatusCodeLabel(ModelType.importsession, session.status) ||
      t`Unknown Status`
    );
  }, [session.status]);

  // Periodically refresh the import session data
  const _interval = useInterval(
    () => {
      session.refreshSession();
    },
    1000,
    {
      autoInvoke: true
    }
  );

  return (
    <Center style={{ height: '100%' }}>
      <Stack gap='xs' align='center' justify='center'>
        <StylishText size='lg'>{statusText}</StylishText>
        <Loader />
      </Stack>
    </Center>
  );
}
