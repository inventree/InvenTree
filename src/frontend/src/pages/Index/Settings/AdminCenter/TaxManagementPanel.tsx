import { t } from '@lingui/core/macro';
import { Stack } from '@mantine/core';

import { StylishText } from '../../../../components/items/StylishText';
import TaxConfigurationTable from '../../../../tables/settings/TaxConfigurationTable';

export default function TaxManagementPanel() {
  return (
    <Stack gap='xs'>
      <StylishText size='lg'>{t`Tax Configurations`}</StylishText>
      <TaxConfigurationTable />
    </Stack>
  );
}
