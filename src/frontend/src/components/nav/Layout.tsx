import { Container, Flex, Space } from '@mantine/core';
import { Navigate, Outlet } from 'react-router-dom';

import { InvenTreeStyle } from '../../globalStyle';
import { useSessionState } from '../../states/SessionState';
import { Footer } from './Footer';
import { Header } from './Header';

export const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const [token] = useSessionState((state) => [state.token]);

  if (!token) {
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
