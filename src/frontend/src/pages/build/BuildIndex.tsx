import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';

import { PageDetail } from '../../components/nav/PageDetail';
import { BuildOrderTable } from '../../components/tables/build/BuildOrderTable';

/**
 * Build Order index page
 */
export default function BuildIndex() {
  return (
    <>
      <Stack>
        <PageDetail title={t`Build Orders`} actions={[]} />
        <BuildOrderTable />
      </Stack>
    </>
  );
}
