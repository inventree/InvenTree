import { i18n } from '@lingui/core';
import { t } from '@lingui/macro';
import { I18nProvider } from '@lingui/react';
import {
  ColorScheme, ColorSchemeProvider, MantineProvider, MantineThemeOverride
} from '@mantine/core';
import { useColorScheme, useLocalStorage } from '@mantine/hooks';
import { ModalsProvider } from '@mantine/modals';
import { NotificationsProvider } from '@mantine/notifications';
import * as Sentry from '@sentry/react';
import { BrowserTracing } from '@sentry/tracing';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import axios from 'axios';
import { useEffect, useState } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { QrCodeModal } from './components/modals/QrCodeModal';
import { useApiState } from './context/ApiState';
import { AuthProvider } from './context/AuthContext';
import { useLocalState } from './context/LocalState';
import { useSessionState } from './context/SessionState';
import { UserProps } from './context/states';
import { defaultHostList } from './defaults';
import ErrorPage from './pages/ErrorPage';
import { Dashboard } from './pages/Index/Dashboard';
import { Home } from './pages/Index/Home';
import { Part } from './pages/Index/Part';
import { Profile } from './pages/Index/Profile/Profile';
import Layout from './pages/layout';
import { Login } from './pages/Login';
import { Logout } from './pages/Logout';
import { activateLocale, loadLocales } from './translation';

// Error tracking
Sentry.init({
  dsn: 'https://84f0c3ea90c64e5092e2bf5dfe325725@o1047628.ingest.sentry.io/4504160008273920',
  integrations: [new BrowserTracing()],
  tracesSampleRate: 1.0
});

// API
export const api = axios.create({});
export function setApiDefaults() {
  const host = useLocalState.getState().host;
  const token = useSessionState.getState().token;

  api.defaults.baseURL = host;
  api.defaults.headers.common['Authorization'] = `Token ${token}`;
}
export const queryClient = new QueryClient();

// States
export async function fetchServerSession() {
  // Fetch user data
  await api.get('/user/me/').then((response) => {
    const user: UserProps = {
      name: `${response.data.first_name} ${response.data.last_name}`,
      email: response.data.email,
      username: response.data.username
    };
    useApiState.getState().setUser(user);
  });
  // Fetch server data
  await api.get('/').then((response) => {
    useApiState.getState().setServer(response.data);
  });
}

// Routes
const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    errorElement: <ErrorPage />,
    children: [
      { index: true, element: <Dashboard /> },
      {
        path: 'home/',
        element: <Home />
      },
      {
        path: 'part/',
        element: <Part />
      },
      {
        path: '/profile/:tabValue',
        element: <Profile />
      }
    ]
  },
  {
    path: '/login',
    element: <Login />,
    errorElement: <ErrorPage />
  },
  {
    path: '/logout',
    element: <Logout />,
    errorElement: <ErrorPage />
  }
]);

function ThemeContext({ children }: { children: any }) {
  const [primaryColor, whiteColor, blackColor, radius, loader] = useLocalState((state) => [state.primaryColor, state.whiteColor, state.blackColor, state.radius, state.loader]);

  // Color Scheme
  const preferredColorScheme = useColorScheme();
  const [colorScheme, setColorScheme] = useLocalStorage<ColorScheme>({
    key: 'scheme',
    defaultValue: preferredColorScheme
  });
  const toggleColorScheme = (value?: ColorScheme) => {
    setColorScheme(value || (colorScheme === 'dark' ? 'light' : 'dark'));
    myTheme.colorScheme = colorScheme;
  };
  const myTheme: MantineThemeOverride = {
    colorScheme: colorScheme,
    primaryColor: primaryColor,
    white: whiteColor,
    black: blackColor,
    loader: loader,
    defaultRadius: radius,
  };

  return (
    <ColorSchemeProvider
      colorScheme={colorScheme}
      toggleColorScheme={toggleColorScheme}
    >
      <MantineProvider
        theme={myTheme}
        withGlobalStyles
        withNormalizeCSS
      >
        <NotificationsProvider>
          <ModalsProvider labels={{ confirm: t`Submit`, cancel: t`Cancel` }} modals={{ qr: QrCodeModal }}>

            {children}

          </ModalsProvider>
        </NotificationsProvider>
      </MantineProvider>
    </ColorSchemeProvider>
  )
}

// Main App
export default function App() {
  const [hostList, language] = useLocalState((state) => [state.hostList, state.language]);

  // Local state initialization
  if (Object.keys(hostList).length === 0) {
    console.log('Loading default host list');
    useLocalState.setState({ hostList: defaultHostList });
  }
  setApiDefaults();

  // Server Session
  const [fetchedServerSession, setFetchedServerSession] = useState(false);
  const sessionState = useSessionState.getState();
  const [token] = sessionState.token ? [sessionState.token] : [null];
  if (token && !fetchedServerSession) {
    setFetchedServerSession(true);
    fetchServerSession();
  }

  // Language
  loadLocales();
  useEffect(() => { activateLocale(language) }, [language])

  // Main App component
  return (
    <I18nProvider i18n={i18n}>
      <ThemeContext>
        <AuthProvider>
          <QueryClientProvider client={queryClient}>
            <RouterProvider router={router} />
          </QueryClientProvider>
        </AuthProvider>
      </ThemeContext>
    </I18nProvider>
  );
}
