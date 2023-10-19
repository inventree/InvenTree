import { Trans } from '@lingui/macro';
import { Card, Container, Group, Loader, Stack, Text } from '@mantine/core';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { checkLoginState } from '../../functions/auth';

export default function Logged_In() {
  const navigate = useNavigate();

  useEffect(() => {
    checkLoginState(navigate);
  }, []);

  return (
    <>
      <Container>
        <Stack align="center">
          <Card shadow="sm" padding="lg" radius="md">
            <Stack>
              <Text size="lg">
                <Trans>Checking if you are already logged in</Trans>
              </Text>
              <Group position="center">
                <Loader />
              </Group>
            </Stack>
          </Card>
        </Stack>
      </Container>
    </>
  );
}
