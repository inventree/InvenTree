import { Container, Flex, Space } from '@mantine/core';
import { Navigate, Outlet } from 'react-router-dom';

import { hasToken } from '../../functions/auth';
import { InvenTreeStyle } from '../../globalStyle';
import { Footer } from './Footer';
import { Header } from './Header';

export const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  if (!hasToken()) {
    return <Navigate to="/logged-in" replace />;
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
