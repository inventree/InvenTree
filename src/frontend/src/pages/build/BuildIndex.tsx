import { Trans, t } from '@lingui/macro';
import { Button, Group, Stack, Text } from '@mantine/core';
import { IconCirclePlus, IconTools } from '@tabler/icons-react';

import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { PageDetail } from '../../components/nav/PageDetail';
import { BuildOrderTable } from '../../components/tables/build/BuildOrderTable';
import { notYetImplemented } from '../../functions/notifications';

/**
 * Build Order index page
 */
export default function BuildIndex() {
  return (
    <>
      <Stack>
        <PageDetail
          title={t`Build Orders`}
          actions={[
            <Button color="green" onClick={() => notYetImplemented()}>
              <Text>{t`New Build Order`}</Text>
            </Button>
          ]}
        />
        <BuildOrderTable />
      </Stack>
    </>
  );
}
