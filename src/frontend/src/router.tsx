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

export const CategoryDetail = Loadable(
  lazy(() => import('./pages/part/CategoryDetail'))
);
export const PartDetail = Loadable(
  lazy(() => import('./pages/part/PartDetail'))
);

export const LocationDetail = Loadable(
  lazy(() => import('./pages/stock/LocationDetail'))
);

export const StockDetail = Loadable(
  lazy(() => import('./pages/stock/StockDetail'))
);

export const BuildIndex = Loadable(
  lazy(() => import('./pages/build/BuildIndex'))
);
export const BuildDetail = Loadable(
  lazy(() => import('./pages/build/BuildDetail'))
);

export const Scan = Loadable(lazy(() => import('./pages/Index/Scan')));

export const Dashboard = Loadable(
  lazy(() => import('./pages/Index/Dashboard'))
);
export const ErrorPage = Loadable(lazy(() => import('./pages/ErrorPage')));

export const Notifications = Loadable(
  lazy(() => import('./pages/Notifications'))
);

export const Profile = Loadable(
  lazy(() => import('./pages/Index/Profile/Profile'))
);

export const UserSettings = Loadable(
  lazy(() => import('./pages/Index/UserSettings'))
);

export const SystemSettings = Loadable(
  lazy(() => import('./pages/Index/SystemSettings'))
);

export const PluginSettings = Loadable(
  lazy(() => import('./pages/Index/PluginSettings'))
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
      <Route path="notifications/" element={<Notifications />} />,
      <Route path="playground/" element={<Playground />} />,
      <Route path="scan/" element={<Scan />} />,
      <Route path="settings/">
        <Route index element={<SystemSettings />} />
        <Route path="user/" element={<UserSettings />} />
        <Route path="plugin/" element={<PluginSettings />} />
      </Route>
      <Route path="part/">
        <Route index element={<CategoryDetail />} />
        <Route path="category/:id" element={<CategoryDetail />} />
        <Route path=":id/" element={<PartDetail />} />
      </Route>
      <Route path="stock/">
        <Route index element={<LocationDetail />} />
        <Route path="location/:id" element={<LocationDetail />} />
        <Route path="item/:id/" element={<StockDetail />} />
      </Route>
      <Route path="build/">
        <Route index element={<BuildIndex />} />
        <Route path=":id/" element={<BuildDetail />} />
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
