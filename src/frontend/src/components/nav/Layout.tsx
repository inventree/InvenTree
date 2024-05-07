import { t } from '@lingui/macro';
import { Container, Flex, Space } from '@mantine/core';
import { SpotlightProvider } from '@mantine/spotlight';
import { IconSearch } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom';

import { getActions } from '../../defaults/actions';
import { InvenTreeStyle } from '../../globalStyle';
import { useUserState } from '../../states/UserState';
import { Boundary } from '../Boundary';
import { Footer } from './Footer';
import { Header } from './Header';

export const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const location = useLocation();
  const { isLoggedIn } = useUserState();

  if (!isLoggedIn()) {
    return (
      <Navigate to="/logged-in" state={{ redirectFrom: location.pathname }} />
    );
  }

  return children;
};

export default function LayoutComponent() {
  const { classes } = InvenTreeStyle();
  const navigate = useNavigate();
  const location = useLocation();

  const defaultActions = getActions(navigate);
  const [actions, setActions] = useState(defaultActions);
  const [customActions, setCustomActions] = useState<boolean>(false);

  function actionsAreChanging(change: []) {
    if (change.length > defaultActions.length) setCustomActions(true);
    setActions(change);
  }
  useEffect(() => {
    if (customActions) {
      setActions(defaultActions);
      setCustomActions(false);
    }
  }, [location]);

  return (
    <ProtectedRoute>
      <SpotlightProvider
        actions={actions}
        onActionsChange={actionsAreChanging}
        searchIcon={<IconSearch size="1.2rem" />}
        searchPlaceholder={t`Search...`}
        shortcut={['mod + K', '/']}
        nothingFoundMessage={t`Nothing found...`}
      >
        <Flex direction="column" mih="100vh">
          <Header />
          <Container className={classes.layoutContent} size="100%">
            <Boundary label={'layout'}>
              <Outlet />
            </Boundary>
            {/* </ErrorBoundary> */}
          </Container>
          <Space h="xl" />
          <Footer />
        </Flex>
      </SpotlightProvider>
    </ProtectedRoute>
  );
}
