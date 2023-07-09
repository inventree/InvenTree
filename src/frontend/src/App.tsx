import { Trans } from '@lingui/macro';
import { Anchor, Center, Container, Stack, Text, Title } from '@mantine/core';
import { useViewportSize } from '@mantine/hooks';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import axios from 'axios';
import { useState } from 'react';
import { RouterProvider } from 'react-router-dom';

import { useApiState } from './context/ApiState';
import { LanguageContext } from './context/LanguageContext';
import { useLocalState } from './context/LocalState';
import { useSessionState } from './context/SessionState';
import { ThemeContext } from './context/ThemeContext';
import { defaultHostList, docLinks } from './defaults';
import { router } from './router';

// API
export const api = axios.create({});
export function setApiDefaults() {
  const host = useLocalState.getState().host;
  const token = useSessionState.getState().token;

  api.defaults.baseURL = host;
  api.defaults.headers.common['Authorization'] = `Token ${token}`;
}
export const queryClient = new QueryClient();

function checksize() {
  const { height, width } = useViewportSize();
  if (width < 425 || height < 425) return true;
  return false;
}

// Main App
export default function App() {
  const [hostList] = useLocalState((state) => [state.hostList]);
  const [fetchApiState] = useApiState((state) => [state.fetchApiState]);
  const [fetchedServerSession, setFetchedServerSession] = useState(false);

  if (checksize()) return MobileAppView();

  // Local state initialization
  if (Object.keys(hostList).length === 0) {
    console.log('Loading default host list');
    useLocalState.setState({ hostList: defaultHostList });
  }
  setApiDefaults();

  // Server Session
  const sessionState = useSessionState.getState();
  const [token] = sessionState.token ? [sessionState.token] : [null];
  if (token && !fetchedServerSession) {
    setFetchedServerSession(true);
    fetchApiState();
  }

  // Main App component
  return <DesktopAppView />;
}

const BaseContext = ({ children }: { children: any }) => {
  return (
    <LanguageContext>
      <ThemeContext>{children}</ThemeContext>
    </LanguageContext>
  );
};

const DesktopAppView = () => {
  return (
    <BaseContext>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </BaseContext>
  );
};

const MobileAppView = () => {
  return (
    <BaseContext>
      <Center mih="100vh">
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
};
