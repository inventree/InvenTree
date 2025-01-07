import { useEffect } from 'react';
import { BrowserRouter } from 'react-router-dom';

import { api, queryClient } from '../App';
import { ApiProvider } from '../contexts/ApiContext';
import { ThemeContext } from '../contexts/ThemeContext';
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
    <ApiProvider client={queryClient} api={api}>
      <ThemeContext>
        <BrowserRouter basename={base_url}>{routes}</BrowserRouter>
      </ThemeContext>
    </ApiProvider>
  );
}
