import { Trans } from '@lingui/macro';
import {
  ActionIcon,
  Button,
  Card,
  Center,
  Container,
  Divider,
  Group,
  Stack,
  Text
} from '@mantine/core';
import { IconArrowBack, IconExclamationCircle } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';

import { LanguageContext } from '../../contexts/LanguageContext';

export default function ErrorPage({
  title,
  message,
  status
}: Readonly<{
  title: string;
  message: string;
  status?: number;
  redirectMessage?: string;
  redirectTarget?: string;
}>) {
  const navigate = useNavigate();

  return (
    <LanguageContext>
      <Center>
        <Container w='md' miw={400}>
          <Card withBorder shadow='xs' padding='xl' radius='sm'>
            <Card.Section p='lg'>
              <Group gap='xs'>
                <ActionIcon color='red' variant='transparent' size='xl'>
                  <IconExclamationCircle />
                </ActionIcon>
                <Text size='xl'>{title}</Text>
              </Group>
            </Card.Section>
            <Divider />
            <Card.Section p='lg'>
              <Stack gap='md'>
                <Text size='lg'>{message}</Text>
                {status && (
                  <Text>
                    <Trans>Status Code</Trans>: {status}
                  </Text>
                )}
              </Stack>
            </Card.Section>
            <Divider />
            <Card.Section p='lg'>
              <Center>
                <Button
                  variant='outline'
                  color='green'
                  onClick={() => navigate('/')}
                >
                  <Trans>Return to the index page</Trans>
                  <IconArrowBack />
                </Button>
              </Center>
            </Card.Section>
          </Card>
        </Container>
      </Center>
    </LanguageContext>
  );
}
