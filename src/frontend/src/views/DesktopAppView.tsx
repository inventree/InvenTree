import { useEffect } from 'react';
import { BrowserRouter } from 'react-router-dom';

import { ApiProvider } from '@lib/contexts/ApiContext';
import { getBaseUrl } from '@lib/functions';
import { getApi, queryClient } from '@lib/functions/api';
import { useLocalState } from '../../lib/states/LocalState';
import { ThemeContext } from '../contexts/ThemeContext';
import { defaultHostList } from '../defaults/defaultHostList';
import { routes } from '../router';

export default function DesktopAppView() {
  const [hostList] = useLocalState((state) => [state.hostList]);
  const base_url = getBaseUrl();
  const api = getApi();

  useEffect(() => {
    if (Object.keys(hostList).length === 0) {
      useLocalState.setState({ hostList: defaultHostList });
    }
  }, [hostList]);

  return (
    <ApiProvider client={queryClient} api={api}>
      <ThemeContext>
        <BrowserRouter basename={base_url}>{routes}</BrowserRouter>
      </ThemeContext>
    </ApiProvider>
  );
}
