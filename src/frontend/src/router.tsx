import { createBrowserRouter } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import Layout from './pages/layout';
import Loading from './Loading';

// Lazy loading helper
const Loadable = (Component: any) => (props: JSX.IntrinsicAttributes) =>
  (
    <Suspense fallback={<Loading />}>
      <Component {...props} />
    </Suspense>
  );

// Lazy loaded pages
export const Home = Loadable(lazy(() => import('./pages/Index/Home')));
export const ErrorPage = Loadable(lazy(() => import('./pages/ErrorPage')));
export const Dashboard = Loadable(
  lazy(() => import('./pages/Index/Dashboard'))
);
export const Part = Loadable(lazy(() => import('./pages/Index/Part')));
export const Profile = Loadable(
  lazy(() => import('./pages/Index/Profile/Profile'))
);
export const Login = Loadable(lazy(() => import('./pages/Login')));
export const Logout = Loadable(lazy(() => import('./pages/Logout')));

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
