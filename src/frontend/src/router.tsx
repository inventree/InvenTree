import { lazy } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import { Loadable } from './functions/loading';

// Lazy loaded pages
export const LayoutComponent = Loadable(
  lazy(() => import('./components/nav/Layout')),
  true,
  true
);
export const LoginLayoutComponent = Loadable(
  lazy(() => import('./pages/Auth/Layout')),
  true,
  true
);

export const Home = Loadable(lazy(() => import('./pages/Index/Home')));

export const CompanyDetail = Loadable(
  lazy(() => import('./pages/company/CompanyDetail'))
);

export const CustomerDetail = Loadable(
  lazy(() => import('./pages/company/CustomerDetail'))
);

export const SupplierDetail = Loadable(
  lazy(() => import('./pages/company/SupplierDetail'))
);

export const ManufacturerDetail = Loadable(
  lazy(() => import('./pages/company/ManufacturerDetail'))
);

export const SupplierPartDetail = Loadable(
  lazy(() => import('./pages/company/SupplierPartDetail'))
);

export const ManufacturerPartDetail = Loadable(
  lazy(() => import('./pages/company/ManufacturerPartDetail'))
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

export const PurchasingIndex = Loadable(
  lazy(() => import('./pages/purchasing/PurchasingIndex'))
);

export const PurchaseOrderDetail = Loadable(
  lazy(() => import('./pages/purchasing/PurchaseOrderDetail'))
);

export const SalesIndex = Loadable(
  lazy(() => import('./pages/sales/SalesIndex'))
);

export const SalesOrderDetail = Loadable(
  lazy(() => import('./pages/sales/SalesOrderDetail'))
);

export const SalesOrderShipmentDetail = Loadable(
  lazy(() => import('./pages/sales/SalesOrderShipmentDetail'))
);

export const ReturnOrderDetail = Loadable(
  lazy(() => import('./pages/sales/ReturnOrderDetail'))
);

export const Scan = Loadable(lazy(() => import('./pages/Index/Scan')));

export const ErrorPage = Loadable(lazy(() => import('./pages/ErrorPage')));

export const Notifications = Loadable(
  lazy(() => import('./pages/Notifications'))
);

export const UserSettings = Loadable(
  lazy(() => import('./pages/Index/Settings/UserSettings'))
);

export const SystemSettings = Loadable(
  lazy(() => import('./pages/Index/Settings/SystemSettings'))
);

export const AdminCenter = Loadable(
  lazy(() => import('./pages/Index/Settings/AdminCenter/Index'))
);

// Core object
export const CoreIndex = Loadable(lazy(() => import('./pages/core/CoreIndex')));
export const UserDetail = Loadable(
  lazy(() => import('./pages/core/UserDetail'))
);
export const GroupDetail = Loadable(
  lazy(() => import('./pages/core/GroupDetail'))
);

export const NotFound = Loadable(
  lazy(() => import('./components/errors/NotFound'))
);

// Auth
export const Login = Loadable(lazy(() => import('./pages/Auth/Login')));
export const LoggedIn = Loadable(
  lazy(() => import('./pages/Auth/LoggedIn')),
  true,
  true
);
export const Logout = Loadable(lazy(() => import('./pages/Auth/Logout')));
export const Register = Loadable(lazy(() => import('./pages/Auth/Register')));
export const Mfa = Loadable(lazy(() => import('./pages/Auth/MFA')));
export const MfaSetup = Loadable(lazy(() => import('./pages/Auth/MFASetup')));
export const ChangePassword = Loadable(
  lazy(() => import('./pages/Auth/ChangePassword'))
);
export const Reset = Loadable(lazy(() => import('./pages/Auth/Reset')));
export const ResetPassword = Loadable(
  lazy(() => import('./pages/Auth/ResetPassword'))
);
export const VerifyEmail = Loadable(
  lazy(() => import('./pages/Auth/VerifyEmail')),
  true,
  true
);

// Routes
export const routes = (
  <Routes>
    <Route path='*' element={<NotFound />} errorElement={<ErrorPage />} />
    <Route path='/' element={<LayoutComponent />} errorElement={<ErrorPage />}>
      <Route index element={<Home />} />,
      <Route path='home/' element={<Home />} />,
      <Route path='notifications/*' element={<Notifications />} />,
      <Route path='scan/' element={<Scan />} />,
      <Route path='settings/'>
        <Route index element={<Navigate to='admin/' />} />
        <Route path='admin/*' element={<AdminCenter />} />
        <Route path='system/*' element={<SystemSettings />} />
        <Route path='user/*' element={<UserSettings />} />
      </Route>
      <Route path='part/'>
        <Route index element={<Navigate to='category/index/' />} />
        <Route path='category/:id?/*' element={<CategoryDetail />} />
        <Route path=':id/*' element={<PartDetail />} />
      </Route>
      <Route path='stock/'>
        <Route index element={<Navigate to='location/index/' />} />
        <Route path='location/:id?/*' element={<LocationDetail />} />
        <Route path='item/:id/*' element={<StockDetail />} />
      </Route>
      <Route path='manufacturing/'>
        <Route index element={<Navigate to='index/' />} />
        <Route path='index/*' element={<BuildIndex />} />
        <Route path='build-order/:id/*' element={<BuildDetail />} />
      </Route>
      <Route path='purchasing/'>
        <Route index element={<Navigate to='index/' />} />
        <Route path='index/*' element={<PurchasingIndex />} />
        <Route path='purchase-order/:id/*' element={<PurchaseOrderDetail />} />
        <Route path='supplier/:id/*' element={<SupplierDetail />} />
        <Route path='supplier-part/:id/*' element={<SupplierPartDetail />} />
        <Route path='manufacturer/:id/*' element={<ManufacturerDetail />} />
        <Route
          path='manufacturer-part/:id/*'
          element={<ManufacturerPartDetail />}
        />
      </Route>
      <Route path='company/:id/*' element={<CompanyDetail />} />
      <Route path='sales/'>
        <Route index element={<Navigate to='index/' />} />
        <Route path='index/*' element={<SalesIndex />} />
        <Route path='sales-order/:id/*' element={<SalesOrderDetail />} />
        <Route path='shipment/:id/*' element={<SalesOrderShipmentDetail />} />
        <Route path='return-order/:id/*' element={<ReturnOrderDetail />} />
        <Route path='customer/:id/*' element={<CustomerDetail />} />
      </Route>
      <Route path='core/'>
        <Route index element={<Navigate to='index/' />} />
        <Route path='index/*' element={<CoreIndex />} />
        <Route path='user/:id/*' element={<UserDetail />} />
        <Route path='group/:id/*' element={<GroupDetail />} />
      </Route>
    </Route>
    <Route
      path='/'
      element={<LoginLayoutComponent />}
      errorElement={<ErrorPage />}
    >
      <Route path='/login' element={<Login />} />,
      <Route path='/logged-in' element={<LoggedIn />} />
      <Route path='/logout' element={<Logout />} />,
      <Route path='/register' element={<Register />} />,
      <Route path='/mfa' element={<Mfa />} />,
      <Route path='/mfa-setup' element={<MfaSetup />} />,
      <Route path='/change-password' element={<ChangePassword />} />
      <Route path='/reset-password' element={<Reset />} />
      <Route path='/set-password' element={<ResetPassword />} />
      <Route path='/verify-email/:key' element={<VerifyEmail />} />
    </Route>
  </Routes>
);
