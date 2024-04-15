import { t } from '@lingui/macro';
import { Container, Flex, Space } from '@mantine/core';
import { Spotlight } from '@mantine/spotlight';
import { IconSearch } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
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

export default function LayoutComponent() {
  const navigate = useNavigate();
  const location = useLocation();

  const defaultactions = getActions(navigate);
  const [actions, setActions] = useState(defaultactions);
  const [customActions, setCustomActions] = useState<boolean>(false);

  function actionsAreChanging(change: []) {
    if (change.length > defaultactions.length) setCustomActions(true);
    setActions(change);
  }
  useEffect(() => {
    if (customActions) {
      setActions(defaultactions);
      setCustomActions(false);
    }
  }, [location]);

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
          actions={actions}
          //onActionsChange={actionsAreChanging}
          //searchIcon={<IconSearch size="1.2rem" />}
          //searchPlaceholder={t`Search...`}
          shortcut={['mod + K', '/']}
          nothingFound={t`Nothing found...`}
        />
      </Flex>
    </ProtectedRoute>
  );
}
