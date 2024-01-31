import { useViewportSize } from '@mantine/hooks';
import { lazy, useEffect } from 'react';

import { Loadable } from '../functions/loading';
import { useServerApiState } from '../states/ApiState';

function checkMobile() {
  const { height, width } = useViewportSize();
  if (width < 425 || height < 425) return true;
  return false;
}

const MobileAppView = Loadable(lazy(() => import('./MobileAppView')));
const DesktopAppView = Loadable(lazy(() => import('./DesktopAppView')));

// Main App
export default function MainView() {
  useEffect(() => {
    useServerApiState.getState().setAuthenticated(false);
  }, []);

  // Check if mobile
  if (checkMobile()) {
    return <MobileAppView />;
  }

  // Main App component
  return <DesktopAppView />;
}
