import { useState } from 'react';
import { MantineProvider, ColorSchemeProvider, ColorScheme } from '@mantine/core';
import { useColorScheme } from '@mantine/hooks';
import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";
import ErrorPage from './pages/error';
import Layout, { Dashboard, Home, Part } from './pages/layout';

const routes = {
  base: 'https://demo.inventree.org/api',
};

const user = {
  "name": "Matthias Mair",
  "email": "code@mjmair.com",
}

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
