import { Trans } from '@lingui/macro';
import { Card, Container, Group, Loader, Stack, Text } from '@mantine/core';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { doLogout } from '../../functions/auth';

/* Expose a route for explicit logout via URL */
export default function Logout() {
  const navigate = useNavigate();

  useEffect(() => {
    doLogout(navigate);
  }, []);

  return (
    <Container>
      <Stack align='center'>
        <Card shadow='sm' padding='lg' radius='md'>
          <Stack>
            <Text size='lg'>
              <Trans>Logging out</Trans>
            </Text>
            <Group justify='center'>
              <Loader />
            </Group>
          </Stack>
        </Card>
      </Stack>
    </Container>
  );
}
