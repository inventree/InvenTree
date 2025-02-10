import { Trans } from '@lingui/macro';
import {
  BackgroundImage,
  Button,
  Center,
  Container,
  Divider,
  Group,
  Loader,
  Paper,
  Stack
} from '@mantine/core';
import { useEffect, useMemo } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { StylishText } from '../../components/items/StylishText';
import { doLogout } from '../../functions/auth';
import { generateUrl } from '../../functions/urls';
import { useServerApiState } from '../../states/ApiState';

export default function Layout() {
  const [server, fetchServerApiState] = useServerApiState((state) => [
    state.server,
    state.fetchServerApiState
  ]);

  const SplashComponent = useMemo(() => {
    const temp = server.customize?.splash;
    if (temp) {
      return ({ children }: { children: React.ReactNode }) => (
        <BackgroundImage src={generateUrl(temp)}>{children}</BackgroundImage>
      );
    }
    return ({ children }: { children: React.ReactNode }) => <>{children}</>;
  }, [server.customize]);

  // Fetch server data on mount if no server data is present
  useEffect(() => {
    if (server.server === null) {
      fetchServerApiState();
    }
  }, [server]);

  // Main rendering block
  return (
    <SplashComponent>
      <Center mih='100vh'>
        <div
          style={{
            padding: '10px',
            backgroundColor: 'rgba(0,0,0,0.5)',
            boxShadow: '0 0 15px 10px rgba(0,0,0,0.5)'
          }}
        >
          <Container w='md' miw={400}>
            <Outlet />
          </Container>
        </div>
      </Center>
    </SplashComponent>
  );
}

export function Wrapper({
  children,
  titleText,
  logOff = false,
  loader = false,
  smallPadding = false
}: Readonly<{
  children?: React.ReactNode;
  titleText: string;
  logOff?: boolean;
  loader?: boolean;
  smallPadding?: boolean;
}>) {
  const navigate = useNavigate();

  return (
    <Paper p='xl' withBorder miw={425}>
      <Stack gap={smallPadding ? 0 : 'md'}>
        <StylishText size='xl'>{titleText}</StylishText>
        <Divider p='xs' />
        {loader && (
          <Group justify='center'>
            <Loader />
          </Group>
        )}
        {children}
        {logOff && (
          <>
            <Divider p='xs' />
            <Button onClick={() => doLogout(navigate)} color='red'>
              <Trans>Log off</Trans>
            </Button>
          </>
        )}
      </Stack>
    </Paper>
  );
}
