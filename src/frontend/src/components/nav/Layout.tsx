import { t } from '@lingui/macro';
import { Container, Flex, Space } from '@mantine/core';
import { Spotlight, createSpotlight } from '@mantine/spotlight';
import { IconSearch } from '@tabler/icons-react';
import { Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom';

import { getActions } from '../../defaults/actions';
import * as classes from '../../main.css';
import { useSessionState } from '../../states/SessionState';
import { Footer } from './Footer';
import { Header } from './Header';

export const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const [token] = useSessionState((state) => [state.token]);

  const location = useLocation();

  if (!token) {
    return (
      <Navigate to="/logged-in" state={{ redirectFrom: location.pathname }} />
    );
  }

  return children;
};

export const [firstStore, firstSpotlight] = createSpotlight();

export default function LayoutComponent() {
  const navigate = useNavigate();
  const defaultactions = getActions(navigate);

  return (
    <ProtectedRoute>
      <Flex direction="column" mih="100vh">
        <Header />
        <Container className={classes.layoutContent} size="100%">
          <Outlet />
        </Container>
        <Space h="xl" />
        <Footer />
        <Spotlight
          actions={defaultactions}
          store={firstStore}
          //onActionsChange={actionsAreChanging}
          highlightQuery
          searchProps={{
            leftSection: <IconSearch size="1.2rem" />,
            placeholder: t`Search...`
          }}
          shortcut={['mod + K', '/']}
          nothingFound={t`Nothing found...`}
        />
      </Flex>
    </ProtectedRoute>
  );
}
