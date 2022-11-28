import {
  MantineProvider,
  ColorSchemeProvider,
  ColorScheme,
  MantineThemeOverride,
} from '@mantine/core';
import { useColorScheme, useLocalStorage } from '@mantine/hooks';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import ErrorPage from './pages/ErrorPage';
import Layout from './pages/layout';
import { Logout } from './pages/Logout';
import { Login } from './pages/Login';
import { Part } from './pages/Index/Part';
import { Home } from './pages/Index/Home';
import { Profile } from './pages/Index/Profile/Profile';
import { Dashboard } from './pages/Index/Dashboard';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import axios from 'axios';
import { AuthProvider } from './contex/AuthContext';
import { UserProps } from './contex/states';
import { useLocalState } from './contex/LocalState';
import { useSessionState } from './contex/SessionState';
import { useApiState } from './contex/ApiState';
import { defaultHostList } from './defaults';
import * as Sentry from '@sentry/react';
import { BrowserTracing } from '@sentry/tracing';
import { useEffect, useState } from 'react';
import { i18n } from '@lingui/core'
import { I18nProvider } from '@lingui/react'
import { de, en, hu } from "make-plural/plurals";
import { NotificationsProvider } from '@mantine/notifications';

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
export async function fetchSession() {
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

// Translations
export type Locales = 'en' | 'de' | 'hu' | 'pseudo-LOCALE';
export const languages: Locales[] = ['en', 'de', 'hu'];
i18n.loadLocaleData({
  de: { plurals: de },
  en: { plurals: en },
  hu: { plurals: hu },
}
);

export async function activateLocale(locale: Locales) {
  const { messages } = await import(`./locales/${locale}/messages.ts`)
  i18n.load(locale, messages)
  i18n.activate(locale)
}

// Main App
export default function App() {
  const [hostList, primaryColor, whiteColor, blackColor, radius, loader, language] = useLocalState((state) => [state.hostList, state.primaryColor, state.whiteColor, state.blackColor, state.radius, state.loader, state.language]);

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

  // Session initialization
  if (Object.keys(hostList).length === 0) {
    console.log('Loading default host list');
    useLocalState.setState({ hostList: defaultHostList });
  }
  setApiDefaults();
  const [fetchedSession, setFetchedSession] = useState(false);
  const sessionState = useSessionState.getState();
  const [token] = sessionState.token ? [sessionState.token] : [null];
  if (token && !fetchedSession) {
    setFetchedSession(true);
    fetchSession();
  }

  // Language
  useEffect(() => { activateLocale(language) }, [language])

  // Main App component
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
        <I18nProvider i18n={i18n}>
          <NotificationsProvider>
            <AuthProvider>
              <QueryClientProvider client={queryClient}>
                <RouterProvider router={router} />
              </QueryClientProvider>
            </AuthProvider>
          </NotificationsProvider>
        </I18nProvider>
      </MantineProvider>
    </ColorSchemeProvider>
  );
}
