import { Container, Grid, SimpleGrid } from '@mantine/core';

import { AccountDetailPanel } from './AccountDetailPanel';
import { DisplaySettingsPanel } from './DisplaySettingsPanel';
import { UserTheme } from './UserThemePanel';

export function AccountContent() {
  const PRIMARY_COL_HEIGHT = 300;
  const SECONDARY_COL_HEIGHT = PRIMARY_COL_HEIGHT / 2 - 8;

  return (
    <div>
      <SimpleGrid cols={2} spacing="md">
        <Container w="100%">
          <AccountDetailPanel />
        </Container>
        <Grid gutter="md">
          <Grid.Col>
            <UserTheme height={SECONDARY_COL_HEIGHT} />
          </Grid.Col>
          <Grid.Col>
            <DisplaySettingsPanel height={SECONDARY_COL_HEIGHT} />
          </Grid.Col>
        </Grid>
      </SimpleGrid>
    </div>
  );
}
