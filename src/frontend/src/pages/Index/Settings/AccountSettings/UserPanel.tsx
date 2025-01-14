import { Container, Grid, SimpleGrid } from '@mantine/core';

import { AccountDetailPanel } from './AccountDetailPanel';
import { UserTheme } from './UserThemePanel';

export function AccountContent() {
  const PRIMARY_COL_HEIGHT = 300;
  const SECONDARY_COL_HEIGHT = PRIMARY_COL_HEIGHT / 2 - 8;

  return (
    <div>
      <SimpleGrid cols={{ base: 1, md: 2 }} spacing='md'>
        <Container w='100%'>
          <AccountDetailPanel />
        </Container>
        <Grid gutter='md'>
          <Grid.Col>
            <UserTheme height={SECONDARY_COL_HEIGHT} />
          </Grid.Col>
        </Grid>
      </SimpleGrid>
    </div>
  );
}
