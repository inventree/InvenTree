import { Trans } from '@lingui/macro';
import { Anchor, Center, Container, Stack, Text, Title } from '@mantine/core';

import { BaseContext } from '../contexts/BaseContext';
import { docLinks } from '../defaults/links';

export default function MobileAppView() {
  return (
    <BaseContext>
      <Center h="100vh">
        <Container>
          <Stack>
            <Title color="red">
              <Trans>Mobile viewport detected</Trans>
            </Title>
            <Text>
              <Trans>
                Platform UI is optimized for Tablets and Desktops, you can use
                the official app for a mobile experience.
              </Trans>
            </Text>
            <Anchor href={docLinks.app}>
              <Trans>Read the docs</Trans>
            </Anchor>
          </Stack>
        </Container>
      </Center>
    </BaseContext>
  );
}
