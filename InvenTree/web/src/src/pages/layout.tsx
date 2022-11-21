import { Outlet } from 'react-router-dom';
import { Header } from '../components/nav/Header';
import { Container, Flex, Space } from '@mantine/core';

import { Footer } from '../components/nav/Footer';
import { useStyles } from '../globalStyle';
import { ProtectedRoute } from '../contex/AuthContext';

export default function Layout() {
  const { classes } = useStyles();

  return (
    <ProtectedRoute>
      <Flex direction="column" mih="100vh">
        <Header />
        <Container className={classes.content}>
          <Outlet />
        </Container>
        <Space h="xl" />
        <Footer />
      </Flex>
    </ProtectedRoute>
  );
}
