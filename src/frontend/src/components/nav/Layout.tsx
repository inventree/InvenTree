import { Container, Flex, Space } from '@mantine/core';
import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { isLoggedIn } from '../../functions/auth';
import { InvenTreeStyle } from '../../globalStyle';
import { Footer } from './Footer';
import { Header } from './Header';

export const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const location = useLocation();

  if (!isLoggedIn()) {
    return (
      <Navigate to="/logged-in" state={{ redirectFrom: location.pathname }} />
    );
  }

  return children;
};

export default function LayoutComponent() {
  const { classes } = InvenTreeStyle();

  return (
    <ProtectedRoute>
      <Flex direction="column" mih="100vh">
        <Header />
        <Container className={classes.layoutContent} size="100%">
          <Outlet />
        </Container>
        <Space h="xl" />
        <Footer />
      </Flex>
    </ProtectedRoute>
  );
}
