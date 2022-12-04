import { Outlet } from 'react-router-dom';
import { Header } from '../components/nav/Header';
import { Container, Flex, Space } from '@mantine/core';

import { Footer } from '../components/nav/Footer';
import { InvenTreeStyle } from '../globalStyle';
import { ProtectedRoute } from '../context/AuthContext';

export default function Layout() {
  const { classes } = InvenTreeStyle();

  return (
    <ProtectedRoute>
      <Flex direction="column" mih="100vh">
        <Header />
        <Container className={classes.layoutContent}>
          <Outlet />
        </Container>
        <Space h="xl" />
        <Footer />
      </Flex>
    </ProtectedRoute>
  );
}
