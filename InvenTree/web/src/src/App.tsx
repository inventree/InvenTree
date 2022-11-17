import { useState } from 'react';
import { MantineProvider, ColorSchemeProvider, ColorScheme } from '@mantine/core';
import { useColorScheme } from '@mantine/hooks';
import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";
import ErrorPage from './pages/error';
import Layout, { Home, Part } from './pages/layout';
import { Dashboard } from "./pages/Dashboard";
import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'
import axios from 'axios';

import * as Sentry from "@sentry/react";
import { BrowserTracing } from "@sentry/tracing";

// Error tracking
Sentry.init({
  dsn: "https://84f0c3ea90c64e5092e2bf5dfe325725@o1047628.ingest.sentry.io/4504160008273920",
  integrations: [new BrowserTracing()],
  tracesSampleRate: 1.0,
});

// Constants
export const user = {
  "name": "Matthias Mair",
  "email": "code@mjmair.com",
  "username": "mjmair",
  "token": "8a19402acdac08bfa9fe6bf95dad8f5b83e702b3",
}

export const api = axios.create({
  baseURL: `https://demo.inventree.org/api/`,
  headers: {'Authorization': `Token ${user.token}`},
});

const tabs = [
  { text: "Home", name: "home" },
  { text: "Part", name: "part" },
]

const links = {
  links: [
    {
      "link": "https://inventree.org/",
      "label": "Website"
    },
    {
      "link": "https://github.com/invenhost/InvenTree",
      "label": "GitHub"
    },
    {
      "link": "https://demo.inventree.org/",
      "label": "Demo"
    }
  ]
}

const queryClient = new QueryClient()

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout tabs={tabs} links={links} user={user} />,
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
    ],
  },
]);

// Main App
export default function App() {
  const preferredColorScheme = useColorScheme();
  const [colorScheme, setColorScheme] = useState<ColorScheme>(preferredColorScheme);
  const toggleColorScheme = (value?: ColorScheme) =>
    setColorScheme(value || (colorScheme === 'dark' ? 'light' : 'dark'));

  return (
    <ColorSchemeProvider colorScheme={colorScheme} toggleColorScheme={toggleColorScheme}>
      <MantineProvider theme={{ colorScheme }} withGlobalStyles withNormalizeCSS>
        <QueryClientProvider client={queryClient}>
          <RouterProvider router={router} />
        </QueryClientProvider>
      </MantineProvider>
    </ColorSchemeProvider>
  );
}
