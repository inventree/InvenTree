import { useState } from 'react';
import { MantineProvider, ColorSchemeProvider, ColorScheme } from '@mantine/core';
import { useColorScheme } from '@mantine/hooks';
import { Text } from '@mantine/core';
import { ColorToggle } from './components/ColorToggle';
import { HeaderTabs } from './components/HeaderTabs';
import {
  createBrowserRouter,
  RouterProvider,
  Route,
} from "react-router-dom";
import ErrorPage from './pages/error';
import Layout, { Home, Part } from './pages/layout';

const routes = {
  base: 'https://demo.inventree.org/api',
  home: '/',
  error: '/error',
};

const user = {
  "name": "Matthias Mair",
  "email": "code@mjmair.com",
}

const tabs = [
  {text: "Home", name:"home"},
  {text: "Part", name:"part"},
]

const links = [
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

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout tabs={tabs} links={links} user={user} />,
    errorElement: <ErrorPage />,
    children: [
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

export default function App() {
  const preferredColorScheme = useColorScheme();
  const [colorScheme, setColorScheme] = useState<ColorScheme>(preferredColorScheme);
  const toggleColorScheme = (value?: ColorScheme) =>
    setColorScheme(value || (colorScheme === 'dark' ? 'light' : 'dark'));

  return (
    <ColorSchemeProvider colorScheme={colorScheme} toggleColorScheme={toggleColorScheme}>
      <MantineProvider theme={{ colorScheme }} withGlobalStyles withNormalizeCSS>
        <RouterProvider router={router} />
      </MantineProvider>
    </ColorSchemeProvider>
  );
}
