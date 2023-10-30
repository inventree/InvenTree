import { Container, Grid, SimpleGrid } from '@mantine/core';

import { useUserState } from '../../../../states/UserState';
import { AccountDetailPanel } from './AccountDetailPanel';
import { DisplaySettingsPanel } from './DisplaySettingsPanel';
import { UserTheme } from './UserThemePanel';

export function AccountContent() {
  // view
  const PRIMARY_COL_HEIGHT = 300;
  const SECONDARY_COL_HEIGHT = PRIMARY_COL_HEIGHT / 2 - 8;
  const [user] = useUserState((state) => [state.user]);

  return (
    <div>
      <SimpleGrid cols={2} spacing="md">
        <Container w="100%">
          <AccountDetailPanel data={user} />
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
