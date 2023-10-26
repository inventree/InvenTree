import { t } from '@lingui/macro';
import { Button, Stack, Text } from '@mantine/core';

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
            <Button
              key="new-build"
              color="green"
              onClick={() => notYetImplemented()}
            >
              <Text>{t`New Build Order`}</Text>
            </Button>
          ]}
        />
        <BuildOrderTable />
      </Stack>
    </>
  );
}
