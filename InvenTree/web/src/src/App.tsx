import { MantineProvider, ColorSchemeProvider, ColorScheme } from '@mantine/core';
import { useColorScheme, useLocalStorage } from '@mantine/hooks';
import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";
import ErrorPage from './pages/error';
import Layout, { Home, Part, Login, Logout, Profile } from './pages/layout';
import { Dashboard } from "./pages/Dashboard";
import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'
import axios from 'axios';
import { AuthProvider, UserProps } from './contex/AuthContext';

const user: UserProps = {
  name: "Matthias Mair",
  email: "code@mjmair.com",
  username: "mjmair",
};

export const api = axios.create({});

// Static Settings
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

export const hosts = [
  "https://demo.inventree.org",
  "https://sample.app.invenhost.com",
];

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
  {
    path: "/profile",
    element: <Profile />
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
  const preferredColorScheme = useColorScheme();
  const [colorScheme, setColorScheme] = useLocalStorage<ColorScheme>({ key: 'scheme', defaultValue: preferredColorScheme });
  const toggleColorScheme = (value?: ColorScheme) => setColorScheme(value || (colorScheme === 'dark' ? 'light' : 'dark'));

  const queryClient = new QueryClient()

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
