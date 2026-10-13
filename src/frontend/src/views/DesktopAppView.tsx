import { useEffect } from 'react';
import { BrowserRouter, useLocation } from 'react-router-dom';

import { getBaseUrl } from '@lib/functions/Navigation';
import { useShallow } from 'zustand/react/shallow';
import { api, queryClient } from '../App';
import { ApiProvider } from '../contexts/ApiContext';
import { ThemeContext } from '../contexts/ThemeContext';
import { defaultHostList } from '../defaults/defaultHostList';
import { routes } from '../router';
import { useLocalState } from '../states/LocalState';

function RouteObserver() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.dispatchEvent(new Event('cangxu-route-change'));
  }, [pathname]);
  return null;
}

export default function DesktopAppView() {
  const [hostList] = useLocalState(useShallow((state) => [state.hostList]));

  useEffect(() => {
    if (Object.keys(hostList).length === 0) {
      useLocalState.setState({ hostList: defaultHostList });
    }
  }, [hostList]);

  return (
    <ApiProvider client={queryClient} api={api}>
      <ThemeContext>
        <BrowserRouter basename={getBaseUrl()}>
          <RouteObserver />
          {routes}
        </BrowserRouter>
      </ThemeContext>
    </ApiProvider>
  );
}
