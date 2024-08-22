import { Stack } from '@mantine/core';
import { lazy } from 'react';

import { Loadable } from '../../../../functions/loading';

const CurrencyTable = Loadable(
  lazy(() => import('../../../../tables/settings/CurrencyTable'))
);

export default function CurrencyManagmentPanel() {
  return (
    <>
      <Stack gap="xs">
        <CurrencyTable />
      </Stack>
    </>
  );
}
