import { lazy } from 'react';
import { createBrowserRouter } from 'react-router-dom';

import { Loadable } from './Loading';

// Lazy loaded pages
export const Layout = Loadable(lazy(() => import('./pages/layout')));
export const Home = Loadable(lazy(() => import('./pages/Index/Home')));
export const ErrorPage = Loadable(lazy(() => import('./pages/ErrorPage')));
export const Profile = Loadable(
  lazy(() => import('./pages/Index/Profile/Profile'))
);
export const NotFound = Loadable(lazy(() => import('./pages/NotFound')));
export const Login = Loadable(lazy(() => import('./pages/Login')));
export const Logged_In = Loadable(lazy(() => import('./pages/Logged-In')));
export const Reset = Loadable(lazy(() => import('./pages/Reset')));
export const Set_Password = Loadable(
  lazy(() => import('./pages/Set-Password'))
);

// Routes
export const router = createBrowserRouter(
  [
    {
      path: '*',
      element: <NotFound />,
      errorElement: <ErrorPage />
    },
    {
      path: '/',
      element: <Layout />,
      errorElement: <ErrorPage />,
      children: [
        {
          index: true,
          element: <Home />
        },
        {
          path: 'home/',
          element: <Home />
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
      path: '/logged-in',
      element: <Logged_In />,
      errorElement: <ErrorPage />
    },
    {
      path: '/reset-password',
      element: <Reset />,
      errorElement: <ErrorPage />
    },
    {
      path: '/set-password',
      element: <Set_Password />,
      errorElement: <ErrorPage />
    }
  ],
  { basename: '/platform' }
);
