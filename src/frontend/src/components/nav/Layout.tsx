import { t } from '@lingui/macro';
import { Container, Flex, Space } from '@mantine/core';
import { Spotlight, createSpotlight } from '@mantine/spotlight';
import { IconSearch } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom';

import { getActions } from '../../defaults/actions';
import * as classes from '../../main.css';
import { useUserState } from '../../states/UserState';
import { Boundary } from '../Boundary';
import { Footer } from './Footer';
import { Header } from './Header';

export const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const location = useLocation();
  const { isLoggedIn } = useUserState();

  if (!isLoggedIn()) {
    return (
      <Navigate
        to='/logged-in'
        state={{
          redirectUrl: location.pathname,
          queryParams: location.search,
          anchor: location.hash
        }}
      />
    );
  }

  return children;
};

export const [firstStore, firstSpotlight] = createSpotlight();

export default function LayoutComponent() {
  const navigate = useNavigate();
  const location = useLocation();

  const defaultActions = getActions(navigate);
  const [actions, setActions] = useState(defaultActions);
  const [customActions, setCustomActions] = useState<boolean>(false);

  function actionsAreChanging(change: []) {
    if (change.length > defaultActions.length) setCustomActions(true);
    setActions(change);
  }
  // firstStore.subscribe(actionsAreChanging);

  // clear additional actions on location change
  useEffect(() => {
    if (customActions) {
      setActions(defaultActions);
      setCustomActions(false);
    }
  }, [location]);

  return (
    <ProtectedRoute>
      <Flex direction='column' mih='100vh'>
        <Header />
        <Container className={classes.layoutContent} size='100%'>
          <Boundary label={'layout'}>
            <Outlet />
          </Boundary>
          {/* </ErrorBoundary> */}
        </Container>
        <Space h='xl' />
        <Footer />
        <Spotlight
          actions={actions}
          store={firstStore}
          highlightQuery
          searchProps={{
            leftSection: <IconSearch size='1.2rem' />,
            placeholder: t`Search...`
          }}
          shortcut={['mod + K', '/']}
          nothingFound={t`Nothing found...`}
        />
      </Flex>
    </ProtectedRoute>
  );
}
