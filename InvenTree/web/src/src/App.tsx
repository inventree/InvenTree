import { MantineProvider, ColorSchemeProvider, ColorScheme } from '@mantine/core';
import { useColorScheme, useLocalStorage } from '@mantine/hooks';
import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";
import ErrorPage from './pages/error';
import Layout, { Home, Part, Login, Logout } from './pages/layout';
import { Profile } from './pages/Profile';
import { Dashboard } from "./pages/Dashboard";
import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'
import axios from 'axios';
import { AuthProvider } from './contex/AuthContext';
import { useApiState, UserProps, useSessionSettings, useSessionState } from './states';
import { defaultHostList, tabs, links } from './defaults';
import * as Sentry from "@sentry/react";
import { BrowserTracing } from "@sentry/tracing";
import { useState } from 'react';

// Error tracking
Sentry.init({
  dsn: "https://84f0c3ea90c64e5092e2bf5dfe325725@o1047628.ingest.sentry.io/4504160008273920",
  integrations: [new BrowserTracing()],
  tracesSampleRate: 1.0,
});

// API
export const api = axios.create({});
export function setApiDefaults() {
  const host = useSessionSettings.getState().host;
  const token = useSessionState.getState().token;

  api.defaults.baseURL = host;
  api.defaults.headers.common['Authorization'] = `Token ${token}`;
}
export const queryClient = new QueryClient()

// States
export async function fetchSession() {
  // Fetch user data
  await api.get('/user/me/').then((response) => {
    const user: UserProps = {
      name: `${response.data.first_name} ${response.data.last_name}`,
      email: response.data.email,
      username: response.data.username,
    };
    useApiState.getState().setUser(user);
  });
  // Fetch server data
  await api.get('/').then((response) => {useApiState.getState().setServer(response.data)});
}

// Routes
const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout tabs={tabs} links={links} />,
    errorElement: <ErrorPage />,
    children: [
      { index: true, element: <Dashboard /> },
      {
        path: "home/",
        element: <Home />,
      },
      {
        path: "part/",
        element: <Part />,
      },
      {
        path: "/profile/:tabValue",
        element: <Profile />
      },
    ],
  },
  {
    path: "/login",
    element: <Login />
  },
  {
    path: "/logout",
    element: <Logout />
  }
]);

// Main App
export default function App() {
  // Color Scheme
  const preferredColorScheme = useColorScheme();
  const [colorScheme, setColorScheme] = useLocalStorage<ColorScheme>({ key: 'scheme', defaultValue: preferredColorScheme });
  const toggleColorScheme = (value?: ColorScheme) => setColorScheme(value || (colorScheme === 'dark' ? 'light' : 'dark'));

  // Session initialization
  const [hostList] = useSessionSettings(state => [state.hostList]);
  if (Object.keys(hostList).length === 0) {
    console.log('Laoding default host list');
    useSessionSettings.setState({ hostList: defaultHostList });
  }
  setApiDefaults();
  const [fetchedSession, setFetchedSession] = useState(false);
  const [token] = useSessionState.getState().token;
  if (token && !fetchedSession) {
    setFetchedSession(true);
    fetchSession();
  }

  // Main App component
  return (
    <ColorSchemeProvider colorScheme={colorScheme} toggleColorScheme={toggleColorScheme}>
      <MantineProvider theme={{ colorScheme }} withGlobalStyles withNormalizeCSS>
        <AuthProvider>
          <QueryClientProvider client={queryClient}>
            <RouterProvider router={router} />
          </QueryClientProvider>
        </AuthProvider>
      </MantineProvider>
    </ColorSchemeProvider>
  );
}
