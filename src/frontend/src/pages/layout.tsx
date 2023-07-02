import { Container, Flex, Space } from '@mantine/core';
import { Navigate, Outlet } from 'react-router-dom';

import { Footer } from '../components/nav/Footer';
import { Header } from '../components/nav/Header';
import { useSessionState } from '../context/SessionState';
import { InvenTreeStyle } from '../globalStyle';

export const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const [token] = useSessionState((state) => [state.token]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default function Layout() {
  const { classes } = InvenTreeStyle();

  return (
    <ProtectedRoute>
      <Flex direction="column" mih="100vh">
        <Header />
        <Container className={classes.layoutContent} size={'xl'}>
          <Outlet />
        </Container>
        <Space h="xl" />
        <Footer />
      </Flex>
    </ProtectedRoute>
  );
}
