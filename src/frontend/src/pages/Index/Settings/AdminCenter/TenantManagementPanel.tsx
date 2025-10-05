import { t } from '@lingui/core/macro';
import { Stack } from '@mantine/core';

import { StylishText } from '../../../../components/items/StylishText';
import TenantTable from '../../../../tables/settings/TenantTable';

export default function TenantManagementPanel() {
  return (
    <Stack gap='xs'>
      <StylishText size='lg'>{t`Tenants`}</StylishText>
      <TenantTable />
    </Stack>
  );
}
