import { useState } from 'react';
import { MantineProvider, ColorSchemeProvider, ColorScheme } from '@mantine/core';
import { useColorScheme } from '@mantine/hooks';
import { Text } from '@mantine/core';
import { ColorToggle } from './components/ColorToggle';
import { HeaderTabs } from './components/Layout';
import {
  createBrowserRouter,
  RouterProvider,
  Route,
} from "react-router-dom";
import ErrorPage from './pages/error';

const user =  {
    "name": "Matthias Mair",
    "email": "code@mjmair.com",
}

const  tabs = [
    "Home",
    "Orders",
    "Education",
    "Community",
    "Forums",
    "Support",
    "Account",
    "Helpdesk",
    "Settings",
  ]

  const router = createBrowserRouter([
    {
      path: "/",
      element: <div>Hello world!</div>,
      errorElement: <ErrorPage />,
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
      <HeaderTabs tabs={tabs} user={user}></HeaderTabs>
      <RouterProvider router={router} />
      </MantineProvider>
    </ColorSchemeProvider>
  );
}
