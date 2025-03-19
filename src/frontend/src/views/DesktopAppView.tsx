import { useEffect } from 'react';
import { BrowserRouter } from 'react-router-dom';

import { ApiProvider } from '@lib/contexts/ApiContext';
import { getBaseUrl } from '@lib/functions';
import { api, queryClient } from '../App';
import { ThemeContext } from '../contexts/ThemeContext';
import { defaultHostList } from '../defaults/defaultHostList';
import { routes } from '../router';
import { useLocalState } from '../states/LocalState';

export default function DesktopAppView() {
  const [hostList] = useLocalState((state) => [state.hostList]);
  const base_url = getBaseUrl();

  useEffect(() => {
    if (Object.keys(hostList).length === 0) {
      useLocalState.setState({ hostList: defaultHostList });
    }
  }, [hostList]);

  return (
    <ApiProvider client={queryClient} api={api}>
      <ThemeContext>
        <BrowserRouter basename={getBaseUrl()}>{routes}</BrowserRouter>
      </ThemeContext>
    </ApiProvider>
  );
}
