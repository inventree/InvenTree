import { createBrowserRouter } from 'react-router-dom';
import ErrorPage from './pages/ErrorPage';
import { Dashboard } from './pages/Index/Dashboard';
import { Home } from './pages/Index/Home';
import { Part } from './pages/Index/Part';
import { Profile } from './pages/Index/Profile/Profile';
import Layout from './pages/layout';
import { Login } from './pages/Login';
import { Logout } from './pages/Logout';

// Routes
export const router = createBrowserRouter(
  [
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
  ],
  { basename: '/platform' }
);
