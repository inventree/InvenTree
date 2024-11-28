import { Trans } from '@lingui/macro';
import { Divider, Stack } from '@mantine/core';
import { lazy } from 'react';

import { StylishText } from '../../../../components/items/StylishText';
import { GlobalSettingList } from '../../../../components/settings/SettingList';
import { Loadable } from '../../../../functions/loading';

const StocktakeReportTable = Loadable(
  lazy(() => import('../../../../tables/settings/StocktakeReportTable'))
);

export default function StocktakePanel() {
  return (
    <Stack gap='xs'>
      <GlobalSettingList
        keys={[
          'STOCKTAKE_ENABLE',
          'STOCKTAKE_EXCLUDE_EXTERNAL',
          'STOCKTAKE_AUTO_DAYS',
          'STOCKTAKE_DELETE_REPORT_DAYS'
        ]}
      />
      <StylishText size='lg'>
        <Trans>Stocktake Reports</Trans>
      </StylishText>
      <Divider />
      <StocktakeReportTable />
    </Stack>
  );
}
