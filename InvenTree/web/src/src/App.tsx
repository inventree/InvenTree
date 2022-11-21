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
import { useSessionSettings } from './states';
import { defaultHostList, tabs, links } from './defaults';

export const api = axios.create({});
export const queryClient = new QueryClient()

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout tabs={tabs} links={links}/>,
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
  const preferredColorScheme = useColorScheme();
  const [colorScheme, setColorScheme] = useLocalStorage<ColorScheme>({ key: 'scheme', defaultValue: preferredColorScheme });
  const toggleColorScheme = (value?: ColorScheme) => setColorScheme(value || (colorScheme === 'dark' ? 'light' : 'dark'));

  const [hostList] = useSessionSettings(state => [state.hostList]);
  if (Object.keys(hostList).length === 0) {
    console.log('Laoding default host list');
    useSessionSettings.setState({hostList: defaultHostList});
  }

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
