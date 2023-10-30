import { Container, Grid, SimpleGrid, Skeleton } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../../../App';
import { ApiPaths, apiUrl } from '../../../../states/ApiState';
import { AccountDetailPanel } from './AccountDetailPanel';
import { DisplaySettingsPanel } from './DisplaySettingsPanel';
import { UserTheme } from './UserThemePanel';

export function AccountContent() {
  // view
  const PRIMARY_COL_HEIGHT = 300;
  const SECONDARY_COL_HEIGHT = PRIMARY_COL_HEIGHT / 2 - 8;

  // data
  function fetchData() {
    // TODO: Replace this call with the global user state, perhaps?
    return api.get(apiUrl(ApiPaths.user_me)).then((res) => res.data);
  }
  const { isLoading, data } = useQuery({
    queryKey: ['user-me'],
    queryFn: fetchData
  });

  return (
    <div>
      <SimpleGrid cols={2} spacing="md">
        <Container w="100%">
          {isLoading ? (
            <Skeleton height={SECONDARY_COL_HEIGHT} />
          ) : (
            <AccountDetailPanel data={data} />
          )}
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
