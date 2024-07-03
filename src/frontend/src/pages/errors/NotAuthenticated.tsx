import { Trans } from '@lingui/macro';
import { Button, Center, Container, Stack, Text, Title } from '@mantine/core';
import { IconArrowBack } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';

import { LanguageContext } from '../../contexts/LanguageContext';

export default function NotAuthenticated() {
  const navigate = useNavigate();

  return (
    <LanguageContext>
      <Center mih="100vh">
        <Container w="md" miw={400}>
          <Stack>
            <Title>
              <Trans>Not Authenticated</Trans>
            </Title>
            <Text>
              <Trans>You are not logged in.</Trans>
            </Text>
            <Button
              variant="outline"
              color="green"
              onClick={() => navigate('/')}
            >
              <Trans>Go to the login page</Trans>
              <IconArrowBack />
            </Button>
          </Stack>
        </Container>
      </Center>
    </LanguageContext>
  );
}
