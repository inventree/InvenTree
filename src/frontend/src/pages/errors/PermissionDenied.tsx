import { Trans } from '@lingui/macro';
import { Button, Center, Container, Stack, Text, Title } from '@mantine/core';
import { IconArrowBack } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';

import { LanguageContext } from '../../contexts/LanguageContext';

export default function PermissionDenied() {
  const navigate = useNavigate();

  return (
    <LanguageContext>
      <Center mih="100vh">
        <Container w="md" miw={400}>
          <Stack>
            <Title>
              <Trans>Permission Denied</Trans>
            </Title>
            <Text>
              <Trans>You do not have permission to view this page.</Trans>
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
