import { t } from '@lingui/macro';
import { Alert, Loader, Stack, Text } from '@mantine/core';
import { IconLock } from '@tabler/icons-react';
import { useState } from 'react';

import ImporterDrawer from '../../components/importer/ImporterDrawer';
import { useUserState } from '../../states/UserState';
import { BomTable } from '../../tables/bom/BomTable';

export default function PartBomPanel({ part }: { part: any }) {
  const user = useUserState();

  const [importOpened, setImportOpened] = useState<boolean>(false);

  const [selectedSession, setSelectedSession] = useState<number | undefined>(
    undefined
  );

  if (!part.pk) {
    return <Loader />;
  }

  return (
    <>
      <Stack gap="xs">
        {part?.locked && (
          <Alert
            title={t`Part is Locked`}
            color="orange"
            icon={<IconLock />}
            p="xs"
          >
            <Text>{t`Bill of materials cannot be edited, as the part is locked`}</Text>
          </Alert>
        )}
        <BomTable part={part} />
      </Stack>
      <ImporterDrawer
        sessionId={selectedSession ?? -1}
        opened={selectedSession != undefined && importOpened}
        onClose={() => {
          setSelectedSession(undefined);
          setImportOpened(false);
          // TODO: Refresh / reload the BOM table
        }}
      />
    </>
  );
}
