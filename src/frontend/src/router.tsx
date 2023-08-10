import { lazy } from 'react';
import { Route, Routes } from 'react-router-dom';

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
export const PurchaseOrderIndex = Loadable(
  lazy(() => import('./pages/order/PurchaseOrderIndex'))
);
export const PurchaseOrderDetail = Loadable(
  lazy(() => import('./pages/order/PurchaseOrderDetail'))
);

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
export const routes = (
  <Routes>
    <Route path="*" element={<NotFound />} errorElement={<ErrorPage />} />
    <Route path="/" element={<LayoutComponent />} errorElement={<ErrorPage />}>
      <Route index element={<Home />} />,
      <Route path="home/" element={<Home />} />,
      <Route path="dashboard/" element={<Dashboard />} />,
      <Route path="playground/" element={<Playground />} />,
      <Route path="parts/" element={<Parts />} />
      <Route path="stock/" element={<Stock />} />,
      <Route path="build/" element={<Build />} />,
      <Route path="order/">
        <Route path="purchase-order/">
          <Route index element={<PurchaseOrderIndex />} />
          <Route path=":pk/" element={<PurchaseOrderDetail />} />
        </Route>
      </Route>
      <Route path="/profile/:tabValue" element={<Profile />} />
    </Route>
    <Route path="/" errorElement={<ErrorPage />}>
      <Route path="/login" element={<Login />} />,
      <Route path="/logged-in" element={<Logged_In />} />
      <Route path="/reset-password" element={<Reset />} />
      <Route path="/set-password" element={<Set_Password />} />
    </Route>
  </Routes>
);
