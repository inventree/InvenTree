import { Trans } from '@lingui/macro';
import {
  Button,
  Center,
  Container,
  Divider,
  Group,
  Loader,
  Paper,
  Stack
} from '@mantine/core';
import { Outlet, useNavigate } from 'react-router-dom';
import SplashScreen from '../../components/SplashScreen';
import { StylishText } from '../../components/items/StylishText';
import { doLogout } from '../../functions/auth';

export default function Layout() {
  return (
    <SplashScreen>
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
    </SplashScreen>
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
