import { Trans } from '@lingui/react/macro';
import { Anchor, Center, Container, Stack, Text, Title } from '@mantine/core';

import { useShallow } from 'zustand/react/shallow';
import { ThemeContext } from '../contexts/ThemeContext';
import { docLinks } from '../defaults/links';
import { IS_DEV } from '../main';
import { useLocalState } from '../states/LocalState';

export default function MobileAppView() {
  const [setAllowMobile] = useLocalState(
    useShallow((state) => [state.setAllowMobile])
  );

  function ignore() {
    setAllowMobile(true);
    window.location.reload();
  }
  return (
    <ThemeContext>
      <Center h='100vh'>
        <Container>
          <Stack>
            <Title c='red'>
              <Trans>Mobile viewport detected</Trans>
            </Title>
            <Text>
              <Trans>
                InvenTree UI is optimized for Tablets and Desktops, you can use
                the official app for a mobile experience.
              </Trans>
            </Text>
            <Anchor href={docLinks.app}>
              <Trans>Read the docs</Trans>
            </Anchor>
            {IS_DEV && (
              <Text onClick={ignore}>
                <Trans>Ignore and continue to Desktop view</Trans>
              </Text>
            )}
          </Stack>
        </Container>
      </Center>
    </ThemeContext>
  );
}
