import { lazy } from 'react';
import { createBrowserRouter } from 'react-router-dom';

import { Loadable } from './functions/loading';

// Lazy loaded pages
export const LayoutComponent = Loadable(
  lazy(() => import('./components/nav/Layout'))
);
export const Home = Loadable(lazy(() => import('./pages/Index/Home')));
export const Playground = Loadable(
  lazy(() => import('./pages/Index/Playground'))
);
export const Parts = Loadable(lazy(() => import('./pages/Index/Part')));
export const Stock = Loadable(lazy(() => import('./pages/Index/Stock')));
export const Build = Loadable(lazy(() => import('./pages/Index/Build')));

export const Dashboard = Loadable(
  lazy(() => import('./pages/Index/Dashboard'))
);
export const ErrorPage = Loadable(lazy(() => import('./pages/ErrorPage')));
export const Profile = Loadable(
  lazy(() => import('./pages/Index/Profile/Profile'))
);
export const NotFound = Loadable(lazy(() => import('./pages/NotFound')));
export const Login = Loadable(lazy(() => import('./pages/Auth/Login')));
export const Logged_In = Loadable(lazy(() => import('./pages/Auth/Logged-In')));
export const Reset = Loadable(lazy(() => import('./pages/Auth/Reset')));
export const Set_Password = Loadable(
  lazy(() => import('./pages/Auth/Set-Password'))
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
      element: <LayoutComponent />,
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
          path: 'dashboard/',
          element: <Dashboard />
        },
        {
          path: 'playground/',
          element: <Playground />
        },
        {
          path: 'parts/',
          element: <Parts />
        },
        {
          path: 'stock/',
          element: <Stock />
        },
        {
          path: 'build/',
          element: <Build />
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
