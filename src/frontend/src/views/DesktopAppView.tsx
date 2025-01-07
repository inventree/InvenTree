import { useEffect } from 'react';
import { BrowserRouter } from 'react-router-dom';

import { api, queryClient } from '../App';
import { ApiProvider } from '../contexts/ApiContext';
import { BaseContext } from '../contexts/BaseContext';
import { defaultHostList } from '../defaults/defaultHostList';
import { base_url } from '../main';
import { routes } from '../router';
import { useLocalState } from '../states/LocalState';

export default function DesktopAppView() {
  const [hostList] = useLocalState((state) => [state.hostList]);

  useEffect(() => {
    if (Object.keys(hostList).length === 0) {
      useLocalState.setState({ hostList: defaultHostList });
    }
  }, [hostList]);

  return (
    <BaseContext>
      <ApiProvider client={queryClient} api={api}>
        <BrowserRouter basename={base_url}>{routes}</BrowserRouter>
      </ApiProvider>
    </BaseContext>
  );
}
