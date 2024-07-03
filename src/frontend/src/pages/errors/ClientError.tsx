import { Trans } from '@lingui/macro';
import { Button, Center, Container, Stack, Text, Title } from '@mantine/core';
import { IconArrowBack } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';

import { LanguageContext } from '../../contexts/LanguageContext';
import NotAuthenticated from './NotAuthenticated';
import NotFound from './NotFound';
import PermissionDenied from './PermissionDenied';

export default function ClientError({ status }: { status?: number }) {
  const navigate = useNavigate();

  switch (status) {
    case 401:
      return <NotAuthenticated />;
    case 403:
      return <PermissionDenied />;
    case 404:
      return <NotFound />;
    default:
      break;
  }

  // Generic client error
  return (
    <LanguageContext>
      <Center mih="100vh">
        <Container w="md" miw={400}>
          <Stack>
            <Title>
              <Trans>Client Error</Trans>
            </Title>
            <Text>
              <Trans>Client error occurred.</Trans>
            </Text>
            <Button
              variant="outline"
              color="green"
              onClick={() => navigate('/')}
            >
              <Trans>Go to the start page</Trans>
              <IconArrowBack />
            </Button>
          </Stack>
        </Container>
      </Center>
    </LanguageContext>
  );
}
